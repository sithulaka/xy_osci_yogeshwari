import eel
import os
import time
import webbrowser
import json
import threading

# Initialize eel with the web folder
eel.init('/home/kavinda/Desktop/2025/yogeshwari/keyboard_ps/xy osci/web')

# Global variables to track state
is_playing = False
audio_loaded = False

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
    'audioVolume': 0.0,  # Set to mute by default
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
    """Handle keyboard events"""
    if is_pressed:
        print(f"Key pressed: {key}")
    else:
        print(f"Key released: {key}")
    return True

# Audio file handling
@eel.expose
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

def auto_map_keyboard():
    """Automatically map keyboard keys to available audio files"""
    # Standard keyboard key order (QWERTY layout)
    key_rows = [
        ['KeyQ', 'KeyW', 'KeyE', 'KeyR', 'KeyT', 'KeyY', 'KeyU', 'KeyI', 'KeyO', 'KeyP'],
        ['KeyA', 'KeyS', 'KeyD', 'KeyF', 'KeyG', 'KeyH', 'KeyJ', 'KeyK', 'KeyL'],
        ['KeyZ', 'KeyX', 'KeyC', 'KeyV', 'KeyB', 'KeyN', 'KeyM']
    ]
    
    # Number keys
    for i in range(10):
        key_rows[0].append(f'Digit{i}')
    
    # Flatten the array
    keys = [key for row in key_rows for key in row]
    
    # Get available audio files
    audio_files = list_audio_files()
    
    # Create mappings
    for i, audio_file in enumerate(audio_files):
        if i < len(keys):
            filepath = ensure_audio_file_accessible(audio_file)
            if filepath:
                keyboard_mapping[keys[i]] = filepath
                print(f"Auto-mapped {keys[i]} to {filepath}")
    
    print(f"Auto-mapped {min(len(audio_files), len(keys))} keys to audio files")
    return True

# JavaScript function to be exposed to Python
@eel.expose
def js_ready():
    """Called when JavaScript is ready"""
    print("JavaScript is ready. Setting up keyboard synthesizer...")
    try:
        # Auto-map keyboard to available audio files
        auto_map_keyboard()
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
print("Starting keyboard synthesizer")
print("Access the visualizer at: http://localhost:8080")
print("Use the console interface to control the synthesizer")
print("Press keyboard keys to play sounds and visualize them")

eel.start('index.html', mode=None, port=8080, block=True)
