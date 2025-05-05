// Controller script for interfacing with Python Eel

// Audio player elements by key
const audioPlayers = {};
const toneAudioSources = {};  // Store audio context sources for tones
const audioFileQueue = [];    // Queue for audio files to play from assets folder
const keyMapping = {};

// Tell Python that JavaScript is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (typeof eel !== 'undefined') {
            eel.js_ready();
            console.log("JavaScript is ready - requesting initial control values");
            
            // Get initial control values
            eel.get_all_controls()(updateControls);
            
            // Set up periodic control updates (every 500ms)
            setInterval(() => {
                eel.get_all_controls()(updateControls);
            }, 500);
        }
    }, 1000);
    
    // Add key event listener
    document.addEventListener('keydown', function(event) {
        if (event.repeat) return; // Ignore key repeat
        eel.key_pressed(event.code, true);
    });
    
    document.addEventListener('keyup', function(event) {
        eel.key_pressed(event.code, false);
    });
});

// Function to handle playing generated tones from Python
eel.expose(playTone);
function playTone(key, audioPath) {
    console.log(`Playing tone: ${audioPath} for key ${key}`);
    
    // Stop any previously playing tone for this key
    if (toneAudioSources[key]) {
        stopTone(key);
    }
    
    try {
        // Create a new audio element for this tone
        const audioElement = new Audio(audioPath);
        audioElement.loop = true; // Loop the tone while key is pressed
        
        // Store for later cleanup
        audioPlayers[key] = audioElement;
        
        // Play the tone
        audioElement.play().catch(err => {
            console.error("Error playing tone:", err);
        });
        
        // If AudioSystem is initialized, connect to oscilloscope
        if (typeof AudioSystem !== 'undefined' && AudioSystem.audioContext && AudioSystem.scopeNode) {
            const source = AudioSystem.audioContext.createMediaElementSource(audioElement);
            source.connect(AudioSystem.scopeNode);
            toneAudioSources[key] = source;
        }
        
        return true;
    } catch (e) {
        console.error("Error in playTone:", e);
        return false;
    }
}

// Function to stop playing a tone
eel.expose(stopTone);
function stopTone(key) {
    console.log(`Stopping tone for key ${key}`);
    
    if (audioPlayers[key]) {
        try {
            // Stop the audio
            audioPlayers[key].pause();
            audioPlayers[key].currentTime = 0;
            
            // Disconnect the audio source if connected
            if (toneAudioSources[key]) {
                try {
                    toneAudioSources[key].disconnect();
                } catch (e) {
                    console.warn("Could not disconnect audio source:", e);
                }
                delete toneAudioSources[key];
            }
            
            delete audioPlayers[key];
            return true;
        } catch (e) {
            console.error("Error stopping tone:", e);
            return false;
        }
    }
    return false;
}

// Update controls with values from Python
function updateControls(newControls) {
    for (const [key, value] of Object.entries(newControls)) {
        if (controls.hasOwnProperty(key)) {
            controls[key] = value;
        }
    }
    
    // Initialize the system if this is the first controls update
    if (!window.isInitialized) {
        initializeOscilloscope();
        window.isInitialized = true;
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
