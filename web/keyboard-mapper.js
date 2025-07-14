class KeyboardAudioManager {
    constructor() {
        this.audioContext = null;
        this.audioBuffers = {};
        this.activeNotes = {};
        this.config = null;
        this.scopeNode = null;
        this.outputNode = null;
        this.pressedKeys = new Set();
    }

    async init() {
        try {
            // Load configurations
            this.config = await this.loadConfig();
            
            // Wait for AudioSystem to be initialized
            this.audioContext = AudioSystem.audioContext;
            this.scopeNode = AudioSystem.scopeNode;
            this.outputNode = AudioSystem.audioVolumeNode;
            
            // Preload all audio files
            await this.preloadAudioFiles();
            
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


    async preloadAudioFiles() {
        const loadPromises = [];
        
        for (const [key, filepath] of Object.entries(this.config.mappings)) {
            const loadPromise = this.loadAudioFile(key, filepath);
            loadPromises.push(loadPromise);
        }
        
        await Promise.all(loadPromises);
        console.log(`Loaded ${Object.keys(this.audioBuffers).length} audio files`);
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


    setupKeyboardListeners() {
        // Connect to Python WebSocket server for hardware key detection
        this.connectToPythonServer();
        
        // Handle window blur to stop all sounds
        window.addEventListener('blur', () => this.stopAllNotes());
    }
    
    connectToPythonServer() {
        const wsUrl = 'ws://localhost:8765';
        console.log(`Connecting to Python key detector at ${wsUrl}`);
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('Connected to Python key detector');
            this.updateConnectionStatus('connected');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('Disconnected from Python key detector');
            this.updateConnectionStatus('disconnected');
            
            // Try to reconnect after 3 seconds
            setTimeout(() => {
                console.log('Attempting to reconnect...');
                this.connectToPythonServer();
            }, 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('error');
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'keydown':
                this.handlePythonKeyDown(data.key);
                break;
            case 'keyup':
                this.handlePythonKeyUp(data.key);
                break;
            case 'status':
                console.log('Key detector status:', data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            switch (status) {
                case 'connected':
                    statusElement.textContent = 'Python Key Detector: Connected';
                    statusElement.style.color = '#00ff00';
                    break;
                case 'disconnected':
                    statusElement.textContent = 'Python Key Detector: Disconnected';
                    statusElement.style.color = '#ff6600';
                    break;
                case 'error':
                    statusElement.textContent = 'Python Key Detector: Error';
                    statusElement.style.color = '#ff0000';
                    break;
            }
        }
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

    handlePythonKeyDown(key) {
        // Ignore if key is already pressed
        if (this.pressedKeys.has(key)) {
            return;
        }
        
        if (this.audioBuffers[key] && !this.activeNotes[key]) {
            // Stop all currently playing notes before starting a new one
            this.stopAllNotes();
            
            this.pressedKeys.add(key);
            this.startNote(key);
            this.updateVisualFeedback();
        }
    }

    handlePythonKeyUp(key) {
        this.pressedKeys.delete(key);
        
        if (this.activeNotes[key]) {
            this.stopNote(key);
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
            
            // Create gain node with normal gain for both display and audio output
            const gainNode = this.audioContext.createGain();
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(
                this.config.settings.defaultVolume, 
                this.audioContext.currentTime + this.config.settings.fadeInTime
            );
            
            // Connect to the existing oscilloscope audio chain for both display and audio
            source.connect(gainNode);
            gainNode.connect(this.scopeNode);
            
            // Start playback
            source.start();
            
            // Store references
            this.activeNotes[key] = {
                source: source,
                gainNode: gainNode
            };
            
            console.log(`Started note with audio: ${key}`);
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
                this.updateVisualFeedback();
            }, this.config.settings.fadeOutTime * 1000);
            
            console.log(`Stopped note: ${key}`);
        } catch (error) {
            console.error(`Failed to stop note ${key}:`, error);
        }
    }


    stopAllNotes() {
        const keys = Object.keys(this.activeNotes);
        keys.forEach(key => this.stopNote(key));
        
        this.pressedKeys.clear();
    }

    updateVisualFeedback() {
        const activeKeysDiv = document.getElementById('activeKeys');
        if (activeKeysDiv) {
            const keys = Object.keys(this.activeNotes);
            
            if (keys.length > 0) {
                activeKeysDiv.textContent = '';
                activeKeysDiv.style.display = 'none';
            } else {
                activeKeysDiv.style.display = 'none';
            }
        }
    }

    updateKeyMapDisplay() {
        const keyMapDiv = document.getElementById('keyMapDisplay');
        if (keyMapDiv && this.config) {
            let html = '<strong>Key Mappings:</strong><br>';
            html += '<div style="margin-bottom: 10px;">Audio Samples (from audio/):</div>';
            for (const [key, filepath] of Object.entries(this.config.mappings)) {
                const filename = filepath.split('/').pop();
                html += `<span style="display: inline-block; margin: 2px 5px; color: #00ff00;">${key.toUpperCase()} → ${filename}</span>`;
            }
            keyMapDiv.innerHTML = html;
        }
    }

    // Public method to get current status
    getStatus() {
        return {
            loadedSamples: Object.keys(this.audioBuffers).length,
            activeSamples: Object.keys(this.activeNotes).length,
            pressedKeys: Array.from(this.pressedKeys),
            isInitialized: this.audioContext !== null
        };
    }
}

// Global instance
let keyboardAudioManager;