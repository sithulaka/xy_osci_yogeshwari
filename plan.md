I'll analyze the provided oscilloscope code and create a comprehensive plan for your keyboard-triggered audio playback requirement.

## Project Analysis & Requirements Documentation

### Current System Overview

The provided code is an XXY Oscilloscope web application that:
- Visualizes audio signals in X-Y mode (Lissajous patterns)
- Supports multiple audio sources: microphone, file upload, and signal generator
- Uses WebGL for rendering with CRT-style effects
- Implements audio processing through Web Audio API

### Your Requirements

1. **Keyboard-to-Audio Mapping**: Map audio files to specific keyboard keys
2. **Press-and-Hold Playback**: Audio plays in loop while key is pressed
3. **Release-to-Stop**: Audio stops when key is released
4. **Integration**: Use existing oscilloscope.js visualization
5. **Configuration**: Separate file for keyboard-audio mappings
6. **Audio Storage**: Audio files in an `/audio` folder

## Phase-by-Phase Implementation Plan

### Phase 1: Project Structure Setup
**Duration**: 30 minutes

1. Create project directory structure:
```
project/
├── index.html (existing)
├── oscilloscope.js (existing)
├── noise.jpg (existing)
├── audio/
│   ├── kick.wav
│   ├── snare.wav
│   ├── hihat.wav
│   └── ... (your audio files)
├── keyboard-mapper.js (new)
└── audio-config.json (new)
```

2. Set up local web server (using Python, Node.js, or other)

### Phase 2: Audio Configuration System
**Duration**: 1 hour

Create `audio-config.json`:
```json
{
  "mappings": {
    "a": "audio/kick.wav",
    "s": "audio/snare.wav",
    "d": "audio/hihat.wav",
    "f": "audio/bass.wav",
    "g": "audio/synth.wav",
    "h": "audio/pad.wav",
    "j": "audio/lead.wav",
    "k": "audio/fx1.wav",
    "l": "audio/fx2.wav",
    "q": "audio/loop1.wav",
    "w": "audio/loop2.wav",
    "e": "audio/loop3.wav"
  },
  "settings": {
    "fadeInTime": 0.01,
    "fadeOutTime": 0.05,
    "defaultVolume": 0.8
  }
}
```

### Phase 3: Keyboard Audio Manager
**Duration**: 2-3 hours

Create `keyboard-mapper.js`:

```javascript
class KeyboardAudioManager {
    constructor() {
        this.audioContext = null;
        this.audioBuffers = {};
        this.activeNotes = {};
        this.config = null;
        this.scopeNode = null;
        this.outputNode = null;
    }

    async init() {
        // Load configuration
        this.config = await this.loadConfig();
        
        // Wait for AudioSystem to be initialized
        this.audioContext = AudioSystem.audioContext;
        this.scopeNode = AudioSystem.scopeNode;
        this.outputNode = AudioSystem.audioVolumeNode;
        
        // Preload all audio files
        await this.preloadAudioFiles();
        
        // Setup keyboard listeners
        this.setupKeyboardListeners();
    }

    async loadConfig() {
        const response = await fetch('audio-config.json');
        return await response.json();
    }

    async preloadAudioFiles() {
        for (const [key, filepath] of Object.entries(this.config.mappings)) {
            try {
                const response = await fetch(filepath);
                const arrayBuffer = await response.arrayBuffer();
                const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
                this.audioBuffers[key] = audioBuffer;
                console.log(`Loaded: ${filepath} for key: ${key}`);
            } catch (error) {
                console.error(`Failed to load ${filepath}:`, error);
            }
        }
    }

    setupKeyboardListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));
    }

    handleKeyDown(event) {
        // Ignore if key is already pressed or if typing in input
        if (event.repeat || event.target.tagName === 'INPUT') return;
        
        const key = event.key.toLowerCase();
        if (this.audioBuffers[key] && !this.activeNotes[key]) {
            this.startNote(key);
        }
    }

    handleKeyUp(event) {
        const key = event.key.toLowerCase();
        if (this.activeNotes[key]) {
            this.stopNote(key);
        }
    }

    startNote(key) {
        const buffer = this.audioBuffers[key];
        if (!buffer) return;

        // Create audio source
        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.loop = true;
        
        // Create gain node for fade in/out
        const gainNode = this.audioContext.createGain();
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(
            this.config.settings.defaultVolume, 
            this.audioContext.currentTime + this.config.settings.fadeInTime
        );
        
        // Connect nodes
        source.connect(gainNode);
        gainNode.connect(this.scopeNode);
        
        // Start playback
        source.start();
        
        // Store references
        this.activeNotes[key] = {
            source: source,
            gainNode: gainNode
        };
    }

    stopNote(key) {
        const note = this.activeNotes[key];
        if (!note) return;

        // Fade out
        const now = this.audioContext.currentTime;
        note.gainNode.gain.cancelScheduledValues(now);
        note.gainNode.gain.setValueAtTime(note.gainNode.gain.value, now);
        note.gainNode.gain.linearRampToValueAtTime(0, now + this.config.settings.fadeOutTime);
        
        // Stop and cleanup
        note.source.stop(now + this.config.settings.fadeOutTime);
        
        // Remove reference after stop
        setTimeout(() => {
            delete this.activeNotes[key];
        }, this.config.settings.fadeOutTime * 1000);
    }
}

// Global instance
let keyboardAudioManager;
```

### Phase 4: Integration with Existing System
**Duration**: 1 hour

Modify `index.html`:
1. Add script reference:
```html
<script src="keyboard-mapper.js"></script>
```

2. Add keyboard controls UI section (after microphone section):
```html
<hr noshade>
<p><b style="font-size:18px">KEYBOARD CONTROL</b>
<div id="keyboardStatus">
    <p>Press keys to play audio samples</p>
    <div id="activeKeys" style="font-family: monospace; color: #00ff00;"></div>
</div>
```

Modify the click handler in `oscilloscope.js`:
```javascript
document.onclick = function() {
    document.onclick = null;
    document.getElementById("clicktostart").remove();
    Filter.init(1024, 8, 6);
    AudioSystem.init(1024);
    Render.setupArrays(Filter.nSmoothedSamples);
    AudioSystem.startSound();
    requestAnimationFrame(drawCRTFrame);
    Controls.setupControls();
    
    // Initialize keyboard audio manager
    keyboardAudioManager = new KeyboardAudioManager();
    keyboardAudioManager.init().then(() => {
        console.log("Keyboard audio manager initialized");
    });
};
```

### Phase 5: Visual Feedback System
**Duration**: 1 hour

Add visual feedback for active keys:

```javascript
// Add to KeyboardAudioManager class
updateVisualFeedback() {
    const activeKeysDiv = document.getElementById('activeKeys');
    const keys = Object.keys(this.activeNotes);
    if (keys.length > 0) {
        activeKeysDiv.textContent = 'Active keys: ' + keys.join(', ').toUpperCase();
        activeKeysDiv.style.display = 'block';
    } else {
        activeKeysDiv.style.display = 'none';
    }
}

// Call in startNote and stopNote methods
```

### Phase 6: Testing & Optimization
**Duration**: 1-2 hours

1. **Test all keyboard mappings**
2. **Verify loop functionality**
3. **Check audio-visual synchronization**
4. **Test multiple simultaneous keys**
5. **Optimize for performance**

### Phase 7: Advanced Features (Optional)
**Duration**: 2-3 hours

1. **Volume control per key**:
```json
{
  "mappings": {
    "a": {
      "file": "audio/kick.wav",
      "volume": 1.0,
      "loop": true
    }
  }
}
```

2. **Visual key map display**:
```javascript
createKeyMapDisplay() {
    const display = document.createElement('div');
    display.id = 'keyMapDisplay';
    display.innerHTML = '<h3>Key Mappings:</h3>';
    
    for (const [key, file] of Object.entries(this.config.mappings)) {
        const filename = file.split('/').pop();
        display.innerHTML += `<div>${key.toUpperCase()} → ${filename}</div>`;
    }
    
    document.getElementById('keyboardStatus').appendChild(display);
}
```

3. **Recording functionality**
4. **MIDI controller support**

## Implementation Notes

### Key Technical Considerations:

1. **Audio Context Integration**: The keyboard system uses the existing AudioSystem.audioContext to ensure proper synchronization with the oscilloscope visualization.

2. **Buffer Management**: Audio files are preloaded as AudioBuffers for instant playback with no latency.

3. **Polyphony**: Multiple keys can play simultaneously without conflicts.

4. **Loop Points**: Native Web Audio API loop functionality ensures seamless looping.

5. **Gain Control**: Fade in/out prevents clicks and pops.

### Potential Challenges:

1. **Browser Autoplay Policy**: Already handled by existing click-to-start mechanism
2. **File Loading**: Implement proper error handling for missing audio files
3. **Performance**: Monitor CPU usage with many simultaneous sounds
4. **Input Conflicts**: Prevent keyboard shortcuts from interfering with form inputs

## Usage Instructions

1. Place audio files in `/audio` folder
2. Configure mappings in `audio-config.json`
3. Start web server
4. Open in browser
5. Click to start (required for Web Audio)
6. Press and hold keys to play sounds
7. Release keys to stop

This modular approach allows easy expansion and modification of the keyboard mapping system while maintaining full integration with the existing oscilloscope visualization.