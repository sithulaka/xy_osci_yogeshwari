import eel
import os
import time
import webbrowser
import json
import threading
import numpy as np
import wave
import struct
import tempfile
from scipy.io import wavfile  # For tone generation

# Initialize eel with the web folder
eel.init('/home/kavinda/Desktop/2025/yogeshwari/keyboard_ps/xy osci/web')

# Global variables to track state
is_playing = False
audio_loaded = False
active_tones = {}  # Track currently playing tones

# Musical note frequencies
NOTE_FREQUENCIES = {
    'C': 261.63,  # C4
    'C#': 277.18,
    'D': 293.66,
    'Eb': 311.13,
    'E': 329.63,
    'F': 349.23,
    'F#': 369.99,
    'G': 392.00,
    'G#': 415.30,
    'A': 440.00,
    'Bb': 466.16,
    'B': 493.88
}

# Audio settings
SAMPLE_RATE = 44100  # samples per second
BUFFER_SIZE = 1024   # buffer size for audio
AMPLITUDE = 0.3      # volume (0.0 to 1.0)

# Key to note mapping
KEY_TO_NOTE = {
    'KeyA': 'C',
    'KeyW': 'C#',
    'KeyS': 'D',
    'KeyE': 'Eb',
    'KeyD': 'E',
    'KeyF': 'F',
    'KeyT': 'F#',
    'KeyG': 'G',
    'KeyY': 'G#',
    'KeyH': 'A',
    'KeyU': 'Bb',
    'KeyJ': 'B',
    'KeyK': 'C',  # C5 (one octave up)
}

# Create tone cache directory
TONE_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web/audio/tones')
os.makedirs(TONE_CACHE_DIR, exist_ok=True)

# Keyboard mapping (key -> audio file)
keyboard_mapping = {
    # Default mappings - will be populated later
}

# Control variables (previously in the UI)
controls = {
    'swapXY': False,
    'sweepOn': False,
    'sweepMsDiv': 1,
    'sweepTriggerValue': 0,
    'signalGeneratorOn': False,
    'mainGain': 0.0,
    'exposureStops': 1.5,  # Increased for better visibility
    'audioVolume': 0.5,  # Set to medium volume for tones
    'hue': 120,  # Green hue for phosphor effect
    'freezeImage': False,
    'disableFilter': False,
    'aValue': 1.0,
    'aExponent': 0.0,
    'bValue': 1.0,
    'bExponent': 0.0,
    'invertXY': False,
    'grid': True,
    'persistence': 0.2,  # Adjusted for clearer phosphor effect
    'xExpression': "sin(2*PI*a*t)*cos(2*PI*b*t)",
    'yExpression': "cos(2*PI*a*t)*cos(2*PI*b*t)",
}

# Generate a sine wave tone file
def generate_tone(frequency, duration=1.0):
    """Generate a sine wave tone WAV file and return its path"""
    
    # Check if we already have this tone cached
    filename = f"{int(frequency)}Hz.wav"
    filepath = os.path.join(TONE_CACHE_DIR, filename)
    
    if os.path.exists(filepath):
        return f"audio/tones/{filename}"
    
    # Generate the tone
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = AMPLITUDE * np.sin(2 * np.pi * frequency * t)
    
    # Apply envelope to avoid clicks
    fade_duration = 0.05  # 50ms fade in/out
    fade_samples = int(fade_duration * SAMPLE_RATE)
    
    # Apply fade in
    if fade_samples > 0:
        fade_in = np.linspace(0, 1, fade_samples)
        tone[:fade_samples] *= fade_in
        
        # Apply fade out
        fade_out = np.linspace(1, 0, fade_samples)
        tone[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    tone = (tone * 32767).astype(np.int16)
    
    # Save as WAV file
    wavfile.write(filepath, SAMPLE_RATE, tone)
    
    print(f"Generated tone file: {filepath}")
    return f"audio/tones/{filename}"

# Generate a more complex waveform combining sine waves for rich oscilloscope patterns
def generate_xy_tone(frequency, harmonics=3, duration=1.0):
    """Generate an XY oscilloscope pattern with harmonics"""
    
    # Check if we already have this tone cached
    filename = f"xy_{int(frequency)}Hz_{harmonics}harm.wav"
    filepath = os.path.join(TONE_CACHE_DIR, filename)
    
    if os.path.exists(filepath):
        return f"audio/tones/{filename}"
    
    # Generate time array
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    
    # Generate X and Y channels for Lissajous patterns
    x_channel = np.zeros_like(t)
    y_channel = np.zeros_like(t)
    
    # Add fundamental frequency
    x_channel += AMPLITUDE * 0.7 * np.sin(2 * np.pi * frequency * t)
    y_channel += AMPLITUDE * 0.7 * np.sin(2 * np.pi * frequency * 1.01 * t)  # Slightly detuned for movement
    
    # Add harmonics
    for i in range(2, harmonics + 2):
        harmonic_freq = frequency * i
        # Different phase and amplitude for each harmonic
        x_channel += AMPLITUDE * (0.3 / i) * np.sin(2 * np.pi * harmonic_freq * t + (i * 0.4))
        y_channel += AMPLITUDE * (0.3 / i) * np.sin(2 * np.pi * harmonic_freq * 1.02 * t)
    
    # Apply envelope to avoid clicks
    fade_duration = 0.05  # 50ms fade in/out
    fade_samples = int(fade_duration * SAMPLE_RATE)
    
    if fade_samples > 0:
        fade_in = np.linspace(0, 1, fade_samples)
        x_channel[:fade_samples] *= fade_in
        y_channel[:fade_samples] *= fade_in
        
        fade_out = np.linspace(1, 0, fade_samples)
        x_channel[-fade_samples:] *= fade_out
        y_channel[-fade_samples:] *= fade_out
    
    # Normalize to prevent clipping
    max_val = max(np.max(np.abs(x_channel)), np.max(np.abs(y_channel)))
    if max_val > 0:
        x_channel = x_channel / max_val * AMPLITUDE
        y_channel = y_channel / max_val * AMPLITUDE
    
    # Interleave channels and convert to 16-bit PCM
    interleaved = np.empty((x_channel.size + y_channel.size,), dtype=x_channel.dtype)
    interleaved[0::2] = x_channel
    interleaved[1::2] = y_channel
    interleaved = (interleaved * 32767).astype(np.int16)
    
    # Create the WAV file
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(interleaved.tobytes())
    
    print(f"Generated XY tone file: {filepath}")
    return f"audio/tones/{filename}"

# Generate all note tones during initialization
def generate_all_note_tones():
    """Pre-generate all note tones for quick access"""
    print("Generating tone files for all notes...")
    
    # Simple tones
    for note, freq in NOTE_FREQUENCIES.items():
        generate_tone(freq)
        
    # XY pattern tones
    for note, freq in NOTE_FREQUENCIES.items():
        generate_xy_tone(freq)
    
    print("All tone files generated.")

# Get the path to a tone file for a given note
def get_tone_path(note, use_xy=True):
    """Get the file path for a given note's tone"""
    if note not in NOTE_FREQUENCIES:
        return None
        
    freq = NOTE_FREQUENCIES[note]
    
    if use_xy:
        return generate_xy_tone(freq)
    else:
        return generate_tone(freq)

# Control commands
@eel.expose
def get_all_controls():
    """Get all control values"""
    return controls

@eel.expose
def set_control(name, value):
    """Set a specific control value"""
    if name in controls:
        old_value = controls[name]
        controls[name] = value
        print(f"Control {name} changed: {old_value} -> {value}")
        return True
    return False

@eel.expose
def toggle_control(name):
    """Toggle a boolean control value"""
    if name in controls and isinstance(controls[name], bool):
        controls[name] = not controls[name]
        print(f"Control {name} toggled to {controls[name]}")
        return controls[name]
    return None

@eel.expose
def get_keyboard_mapping():
    """Get the current keyboard mapping"""
    return keyboard_mapping

@eel.expose
def set_keyboard_mapping(key, audio_file):
    """Set a keyboard mapping"""
    if audio_file:
        # Make sure the audio file exists and is accessible
        audio_path = ensure_audio_file_accessible(audio_file)
        if audio_path:
            keyboard_mapping[key] = audio_path
            print(f"Mapped key {key} to {audio_path}")
            return True
    else:
        # If audio_file is None, remove the mapping
        if key in keyboard_mapping:
            del keyboard_mapping[key]
            print(f"Removed mapping for key {key}")
        return True
    return False

@eel.expose
def key_pressed(key, is_pressed):
    """Handle keyboard events to play tones"""
    if key in KEY_TO_NOTE:
        note = KEY_TO_NOTE[key]
        
        if is_pressed:
            # Start playing the note
            if key not in active_tones:
                tone_path = get_tone_path(note, use_xy=True)  # Use XY patterns
                if tone_path:
                    try:
                        # Correct way to call JavaScript functions
                        eel.playTone(key, tone_path)  # Don't add () here, Eel handles that internally
                        active_tones[key] = note
                        print(f"Playing {note} ({NOTE_FREQUENCIES[note]} Hz)")
                    except Exception as e:
                        print(f"Error playing tone: {e}")
                    return True
        else:
            # Stop playing the note
            if key in active_tones:
                try:
                    # Correct way to call JavaScript functions
                    eel.stopTone(key)  # Don't add () here, Eel handles that internally
                    del active_tones[key]
                    print(f"Stopped {note}")
                except Exception as e:
                    print(f"Error stopping tone: {e}")
                return True
    
    return False

# Audio file handling
def list_audio_files():
    """List all audio files in the audio directory"""
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web/audio')
    
    # Create audio directory if it doesn't exist
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
        return []
    
    # Get all audio files (wav, mp3, ogg)
    audio_files = []
    for ext in ['.wav', '.mp3', '.ogg']:
        audio_files.extend([f for f in os.listdir(audio_dir) if f.lower().endswith(ext)])
    return audio_files

def ensure_audio_file_accessible(filename):
    """Make sure an audio file is accessible from the web directory"""
    try:
        # First check if the file includes the web/audio path
        if filename.startswith('audio/'):
            web_path = os.path.join('web', filename)
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), web_path)
            if os.path.exists(full_path):
                return filename
        
        # Check in web/audio directory
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'audio')
        full_path = os.path.join(audio_dir, os.path.basename(filename))
        
        # If not found in web/audio, check in regular audio directory and copy if needed
        if not os.path.exists(full_path):
            alt_audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
            alt_path = os.path.join(alt_audio_dir, os.path.basename(filename))
            
            if os.path.exists(alt_path):
                # Copy to web/audio
                os.makedirs(audio_dir, exist_ok=True)
                import shutil
                shutil.copy2(alt_path, full_path)
                print(f"Copied audio file {filename} to web directory")
            else:
                # Not found
                print(f"Audio file {filename} not found")
                return None
        
        # Return the web-accessible path
        return f"audio/{os.path.basename(filename)}"
    
    except Exception as e:
        print(f"Error ensuring audio file accessibility: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# JavaScript function to be exposed to Python
@eel.expose
def js_ready():
    """Called when JavaScript is ready"""
    print("JavaScript is ready. Setting up keyboard synthesizer...")
    try:
        # Generate tone files for all notes
        generate_all_note_tones()
        
        # Setup keyboard mapping for notes
        for key, note in KEY_TO_NOTE.items():
            tone_path = get_tone_path(note, use_xy=True)
            keyboard_mapping[key] = tone_path
            
        print("Keyboard synthesizer setup complete")
    except Exception as e:
        print(f"Error setting up keyboard synthesizer: {e}")

# Interactive console interface
def console_interface():
    """Simple console interface to control the oscilloscope"""
    print("\n=== Keyboard Synthesizer Control Console ===")
    print("Type 'help' for available commands")
    
    while True:
        try:
            cmd = input("\n> ").strip().split(' ', 1)
            command = cmd[0].lower() if cmd else ''
            
            if command == 'quit' or command == 'exit':
                print("Exiting console interface...")
                break
            elif command == 'help':
                print("\nAvailable commands:")
                print("  set <control> <value>  - Set a control value")
                print("  get <control>          - Get a control value")
                print("  list controls          - List all controls")
                print("  list files             - List all audio files")
                print("  list keys              - List all key mappings")
                print("  map <key> <file>       - Map a key to an audio file")
                print("  unmap <key>            - Remove a key mapping")
                print("  automap                - Automatically map keys to files")
                print("  quit/exit              - Exit program")
            elif command == 'set':
                if len(cmd) < 2:
                    print("Usage: set <control> <value>")
                    continue
                    
                try:
                    control, value = cmd[1].split(' ', 1)
                    if control in controls:
                        # Convert value to appropriate type
                        current_type = type(controls[control])
                        if current_type == bool:
                            value = value.lower() in ('true', 'yes', '1', 'on', 't')
                        elif current_type == int:
                            value = int(value)
                        elif current_type == float:
                            value = float(value)
                        
                        old_value = controls[control]
                        controls[control] = value
                        print(f"Set {control}: {old_value} -> {value}")
                    else:
                        print(f"Unknown control: {control}")
                except Exception as e:
                    print(f"Error: {str(e)}")
            elif command == 'get':
                if len(cmd) < 2:
                    print("Usage: get <control>")
                    continue
                    
                control = cmd[1]
                if control in controls:
                    print(f"{control} = {controls[control]}")
                else:
                    print(f"Unknown control: {control}")
            elif command == 'list':
                if len(cmd) > 1 and cmd[1] == 'controls':
                    for control, value in controls.items():
                        print(f"{control} = {value}")
                elif len(cmd) > 1 and cmd[1] == 'files':
                    files = list_audio_files()
                    if files:
                        print("Available audio files:")
                        for i, file in enumerate(files):
                            print(f"  {i+1}. {file}")
                    else:
                        print("No audio files found")
                elif len(cmd) > 1 and cmd[1] == 'keys':
                    if keyboard_mapping:
                        print("Current keyboard mappings:")
                        for key, file in keyboard_mapping.items():
                            print(f"  {key} -> {file}")
                    else:
                        print("No keyboard mappings defined")
                else:
                    print("Usage: list [controls|files|keys]")
            elif command == 'map':
                if len(cmd) < 2:
                    print("Usage: map <key> <file>")
                    continue
                    
                try:
                    key, file = cmd[1].split(' ', 1)
                    if set_keyboard_mapping(key, file):
                        print(f"Mapped key {key} to {file}")
                    else:
                        print(f"Failed to map key {key} to {file}")
                except Exception as e:
                    print(f"Error: {str(e)}")
            elif command == 'unmap':
                if len(cmd) < 2:
                    print("Usage: unmap <key>")
                    continue
                    
                key = cmd[1]
                if key in keyboard_mapping:
                    del keyboard_mapping[key]
                    print(f"Removed mapping for key {key}")
                else:
                    print(f"No mapping found for key {key}")
            elif command == 'automap':
                auto_map_keyboard()
                print("Automatically mapped keys to audio files")
            else:
                print(f"Unknown command: {command}")
        except Exception as e:
            print(f"Error: {str(e)}")

# Start the console interface in a separate thread
console_thread = threading.Thread(target=console_interface, daemon=True)
console_thread.start()

# Start Eel with the main HTML file
print("Starting keyboard synthesizer with tone generation")
print("Access the visualizer at: http://localhost:8080")
print("Press A, W, S, E, D, F, T, G, Y, H, U, J, K for piano notes")

eel.start('index.html', mode=None, port=8080, block=True)
