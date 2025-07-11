class KeyboardAudioManager {
    constructor() {
        this.audioContext = null;
        this.audioBuffers = {};
        this.toneBuffers = {};
        this.activeNotes = {};
        this.activeTones = {};
        this.config = null;
        this.toneConfig = null;
        this.scopeNode = null;
        this.outputNode = null;
        this.pressedKeys = new Set();
        this.originalAudioVolume = undefined;
    }

    async init() {
        try {
            // Load configurations
            this.config = await this.loadConfig();
            this.toneConfig = await this.loadToneConfig();
            
            // Wait for AudioSystem to be initialized
            this.audioContext = AudioSystem.audioContext;
            this.scopeNode = AudioSystem.scopeNode;
            this.outputNode = AudioSystem.audioVolumeNode;
            
            // Preload all audio files
            await this.preloadAudioFiles();
            await this.preloadToneFiles();
            
            // Setup keyboard listeners
            this.setupKeyboardListeners();
            
            // Setup visual feedback
            this.setupVisualFeedback();
            
            console.log("Keyboard audio manager initialized successfully");
            this.updateKeyMapDisplay();
        } catch (error) {
            console.error("Failed to initialize keyboard audio manager:", error);
        }
    }

    async loadConfig() {
        const response = await fetch('audio-config.json');
        return await response.json();
    }

    async loadToneConfig() {
        const response = await fetch('tone-config.json');
        return await response.json();
    }

    async preloadAudioFiles() {
        const loadPromises = [];
        
        for (const [key, filepath] of Object.entries(this.config.mappings)) {
            const loadPromise = this.loadAudioFile(key, filepath);
            loadPromises.push(loadPromise);
        }
        
        await Promise.all(loadPromises);
        console.log(`Loaded ${Object.keys(this.audioBuffers).length} audio files`);
    }

    async preloadToneFiles() {
        const loadPromises = [];
        
        for (const [key, filepath] of Object.entries(this.toneConfig.mappings)) {
            const loadPromise = this.loadToneFile(key, filepath);
            loadPromises.push(loadPromise);
        }
        
        await Promise.all(loadPromises);
        console.log(`Loaded ${Object.keys(this.toneBuffers).length} tone files`);
    }

    async loadAudioFile(key, filepath) {
        try {
            const response = await fetch(filepath);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            this.audioBuffers[key] = audioBuffer;
            console.log(`Loaded audio: ${filepath} for key: ${key}`);
        } catch (error) {
            console.error(`Failed to load ${filepath}:`, error);
        }
    }

    async loadToneFile(key, filepath) {
        try {
            const response = await fetch(filepath);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            this.toneBuffers[key] = audioBuffer;
            console.log(`Loaded tone: ${filepath} for key: ${key}`);
        } catch (error) {
            console.error(`Failed to load tone ${filepath}:`, error);
        }
    }

    setupKeyboardListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));
        
        // Handle window blur to stop all sounds
        window.addEventListener('blur', () => this.stopAllNotes());
    }

    setupVisualFeedback() {
        // Visual feedback will be added to existing DOM
        const keyboardStatus = document.getElementById('keyboardStatus');
        if (keyboardStatus) {
            keyboardStatus.innerHTML = `
                <div id="activeKeys" style="font-family: monospace; color: #00ff00; margin: 5px 0;"></div>
                <div id="keyMapDisplay" style="font-size: 10px; color: #666; margin-top: 10px;"></div>
            `;
        }
    }

    handleKeyDown(event) {
        // Ignore if key is already pressed or if typing in input
        if (this.pressedKeys.has(event.code) || event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        const key = event.key.toLowerCase();
        if (this.audioBuffers[key] && !this.activeNotes[key]) {
            // Stop all currently playing notes before starting a new one
            this.stopAllNotes();
            
            this.pressedKeys.add(event.code);
            this.startNote(key);
            this.startTone(key);
            this.updateVisualFeedback();
        }
    }

    handleKeyUp(event) {
        this.pressedKeys.delete(event.code);
        
        const key = event.key.toLowerCase();
        if (this.activeNotes[key]) {
            this.stopNote(key);
            this.stopTone(key);
            this.updateVisualFeedback();
        }
    }

    startNote(key) {
        const buffer = this.audioBuffers[key];
        if (!buffer) return;

        try {
            // Create audio source
            const source = this.audioContext.createBufferSource();
            source.buffer = buffer;
            source.loop = true;
            
            // Create gain node with normal gain for oscilloscope display
            const gainNode = this.audioContext.createGain();
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(
                this.config.settings.defaultVolume, 
                this.audioContext.currentTime + this.config.settings.fadeInTime
            );
            
            // Connect to the existing oscilloscope audio chain (same as original)
            source.connect(gainNode);
            gainNode.connect(this.scopeNode);
            
            // Temporarily store original audio volume and mute it
            if (!this.originalAudioVolume) {
                this.originalAudioVolume = controls.audioVolume;
            }
            controls.audioVolume = 0; // Mute the final output
            
            // Start playback
            source.start();
            
            // Store references
            this.activeNotes[key] = {
                source: source,
                gainNode: gainNode
            };
            
            console.log(`Started note (display only): ${key}`);
        } catch (error) {
            console.error(`Failed to start note ${key}:`, error);
        }
    }

    stopNote(key) {
        const note = this.activeNotes[key];
        if (!note) return;

        try {
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
                
                // If no more audio notes are playing, restore original audio volume
                if (Object.keys(this.activeNotes).length === 0 && this.originalAudioVolume !== undefined) {
                    controls.audioVolume = this.originalAudioVolume;
                    this.originalAudioVolume = undefined;
                }
                
                this.updateVisualFeedback();
            }, this.config.settings.fadeOutTime * 1000);
            
            console.log(`Stopped note: ${key}`);
        } catch (error) {
            console.error(`Failed to stop note ${key}:`, error);
        }
    }

    startTone(key) {
        const buffer = this.toneBuffers[key];
        if (!buffer) return;

        try {
            // Create audio source
            const source = this.audioContext.createBufferSource();
            source.buffer = buffer;
            source.loop = true;
            
            // Create gain node for fade in/out
            const gainNode = this.audioContext.createGain();
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(
                this.toneConfig.settings.defaultVolume, 
                this.audioContext.currentTime + this.toneConfig.settings.fadeInTime
            );
            
            // Connect directly to audio destination, bypassing the main volume control
            source.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Start playback
            source.start();
            
            // Store references
            this.activeTones[key] = {
                source: source,
                gainNode: gainNode
            };
            
            console.log(`Started tone: ${key}`);
        } catch (error) {
            console.error(`Failed to start tone ${key}:`, error);
        }
    }

    stopTone(key) {
        const tone = this.activeTones[key];
        if (!tone) return;

        try {
            // Fade out
            const now = this.audioContext.currentTime;
            tone.gainNode.gain.cancelScheduledValues(now);
            tone.gainNode.gain.setValueAtTime(tone.gainNode.gain.value, now);
            tone.gainNode.gain.linearRampToValueAtTime(0, now + this.toneConfig.settings.fadeOutTime);
            
            // Stop and cleanup
            tone.source.stop(now + this.toneConfig.settings.fadeOutTime);
            
            // Remove reference after stop
            setTimeout(() => {
                delete this.activeTones[key];
            }, this.toneConfig.settings.fadeOutTime * 1000);
            
            console.log(`Stopped tone: ${key}`);
        } catch (error) {
            console.error(`Failed to stop tone ${key}:`, error);
        }
    }

    stopAllNotes() {
        const keys = Object.keys(this.activeNotes);
        keys.forEach(key => this.stopNote(key));
        
        const toneKeys = Object.keys(this.activeTones);
        toneKeys.forEach(key => this.stopTone(key));
        
        // Restore original audio volume immediately when stopping all
        if (this.originalAudioVolume !== undefined) {
            controls.audioVolume = this.originalAudioVolume;
            this.originalAudioVolume = undefined;
        }
        
        this.pressedKeys.clear();
    }

    updateVisualFeedback() {
        const activeKeysDiv = document.getElementById('activeKeys');
        if (activeKeysDiv) {
            const keys = Object.keys(this.activeNotes);
            const toneKeys = Object.keys(this.activeTones);
            const allKeys = [...new Set([...keys, ...toneKeys])];
            
            if (allKeys.length > 0) {
                activeKeysDiv.textContent = '';
                activeKeysDiv.style.display = 'none';
            } else {
                activeKeysDiv.style.display = 'none';
            }
        }
    }

    updateKeyMapDisplay() {
        const keyMapDiv = document.getElementById('keyMapDisplay');
        if (keyMapDiv && this.config && this.toneConfig) {
            let html = '<strong>Key Mappings:</strong><br>';
            html += '<div style="margin-bottom: 10px;">Oscilloscope Display (from audio/):</div>';
            for (const [key, filepath] of Object.entries(this.config.mappings)) {
                const filename = filepath.split('/').pop();
                html += `<span style="display: inline-block; margin: 2px 5px; color: #00ff00;">${key.toUpperCase()} → ${filename}</span>`;
            }
            html += '<div style="margin: 10px 0 5px 0;">Tone Playback (from tones/):</div>';
            for (const [key, filepath] of Object.entries(this.toneConfig.mappings)) {
                const filename = filepath.split('/').pop();
                html += `<span style="display: inline-block; margin: 2px 5px; color: #ffaa00;">${key.toUpperCase()} → ${filename}</span>`;
            }
            keyMapDiv.innerHTML = html;
        }
    }

    // Public method to get current status
    getStatus() {
        return {
            loadedSamples: Object.keys(this.audioBuffers).length,
            loadedTones: Object.keys(this.toneBuffers).length,
            activeSamples: Object.keys(this.activeNotes).length,
            activeTones: Object.keys(this.activeTones).length,
            pressedKeys: Array.from(this.pressedKeys),
            isInitialized: this.audioContext !== null
        };
    }
}

// Global instance
let keyboardAudioManager;