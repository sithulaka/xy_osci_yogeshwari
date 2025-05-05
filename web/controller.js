// Controller script for interfacing with Python Eel

// Flag to track initialization
let isInitialized = false;

// Audio player elements by key
const audioPlayers = {};
const keyMapping = {};

// Tell Python that JavaScript is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the audio container
    createAudioContainer();
    
    // A small delay to ensure everything is loaded
    setTimeout(() => {
        if (typeof eel !== 'undefined') {
            eel.js_ready();
            console.log("JavaScript is ready - requesting initial control values");
            
            // Get initial control values
            eel.get_all_controls()(updateControls);
            
            // Get keyboard mappings
            eel.get_keyboard_mapping()(updateKeyboardMapping);
            
            // Set up periodic control updates (every 500ms)
            setInterval(() => {
                eel.get_all_controls()(updateControls);
            }, 500);
        }
    }, 1000);
    
    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
});

// Create a container for all audio elements
function createAudioContainer() {
    const container = document.createElement('div');
    container.id = 'audioContainer';
    container.style.display = 'none';
    document.body.appendChild(container);
}

// Update keyboard mapping
function updateKeyboardMapping(mapping) {
    Object.assign(keyMapping, mapping);
    console.log("Keyboard mapping updated:", keyMapping);
}

// Handle key press
function handleKeyDown(event) {
    if (event.repeat) return; // Prevent repeated triggers while holding key
    
    const key = event.code;
    if (keyMapping[key]) {
        eel.key_pressed(key, true);
        playSound(key, keyMapping[key]);
    }
}

// Handle key release
function handleKeyUp(event) {
    const key = event.code;
    if (keyMapping[key]) {
        eel.key_pressed(key, false);
        stopSound(key);
    }
}

// Play a sound for a specific key
function playSound(key, audioFile) {
    console.log(`Playing ${audioFile} for key ${key}`);
    
    // Create or get the audio element for this key
    let audioElement = audioPlayers[key];
    
    // If no audio element exists for this key, create one
    if (!audioElement) {
        audioElement = new Audio();
        audioElement.id = `audio-${key}`;
        audioElement.loop = false;
        audioPlayers[key] = audioElement;
        
        // Add to the DOM (hidden)
        const container = document.getElementById('audioContainer');
        container.appendChild(audioElement);
    }
    
    // Set source and play
    audioElement.src = audioFile;
    audioElement.currentTime = 0;
    
    // Connect to oscilloscope
    connectAudioToOscilloscope(audioElement, key);
    
    // Play the audio
    const playPromise = audioElement.play();
    if (playPromise) {
        playPromise.catch(error => {
            console.error(`Error playing audio for ${key}:`, error);
        });
    }
}

// Stop a sound for a specific key
function stopSound(key) {
    const audioElement = audioPlayers[key];
    if (audioElement) {
        audioElement.pause();
        audioElement.currentTime = 0;
    }
}

// Connect audio to oscilloscope
function connectAudioToOscilloscope(audioElement, key) {
    // Only connect if this is the first audio element
    if (!AudioSystem.sourceMap) {
        AudioSystem.sourceMap = {};
    }
    
    // If we already have a connection for this key, disconnect it
    if (AudioSystem.sourceMap[key]) {
        AudioSystem.sourceMap[key].disconnect();
    }
    
    try {
        // Create a new audio source from the element
        const source = AudioSystem.audioContext.createMediaElementSource(audioElement);
        
        // Connect to the scope node
        source.connect(AudioSystem.scopeNode);
        
        // Store the source
        AudioSystem.sourceMap[key] = source;
        
        console.log(`Connected audio for key ${key} to oscilloscope`);
    } catch (e) {
        console.error(`Error connecting audio to oscilloscope: ${e.message}`);
    }
}

// Function to load an audio file
eel.expose(loadAudioFile);
function loadAudioFile(filepath) {
    console.log(`Loading audio file: ${filepath}`);
    return true;
}

// Update controls with values from Python
function updateControls(newControls) {
    for (const [key, value] of Object.entries(newControls)) {
        if (controls.hasOwnProperty(key)) {
            controls[key] = value;
        }
    }
    
    // Initialize the system if this is the first controls update
    if (!isInitialized) {
        initializeOscilloscope();
        isInitialized = true;
    }
}

// Initialize oscilloscope system once controls are received
function initializeOscilloscope() {
    console.log("Initializing oscilloscope with controls from Python");
    
    try {
        // Initialize components (these functions are defined in oscilloscope.js)
        UI.init();
        Render.init();
        Filter.init(1024, 8, 6);
        AudioSystem.init(1024);
        Render.setupArrays(Filter.nSmoothedSamples);
        AudioSystem.startSound();
        
        // Start animation frame rendering
        requestAnimationFrame(drawCRTFrame);
    } catch (e) {
        console.error("Error initializing oscilloscope:", e);
    }
}

// Expose a function to assign a key mapping
eel.expose(assignKeyMapping);
function assignKeyMapping(key, audioFile) {
    keyMapping[key] = audioFile;
    console.log(`Assigned ${audioFile} to key ${key}`);
    return true;
}

// Expose a function to remove a key mapping
eel.expose(removeKeyMapping);
function removeKeyMapping(key) {
    if (keyMapping[key]) {
        delete keyMapping[key];
        console.log(`Removed mapping for key ${key}`);
        return true;
    }
    return false;
}
