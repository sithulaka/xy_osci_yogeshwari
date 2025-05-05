#!/usr/bin/env python3
"""
Tool to map audio files to keyboard keys for the oscilloscope synthesizer
"""
import os
import json
import glob
import shutil

# Define keyboard keys (standard QWERTY layout)
KEYBOARD_KEYS = [
    # First row - numbers
    'Digit1', 'Digit2', 'Digit3', 'Digit4', 'Digit5', 'Digit6', 'Digit7', 'Digit8', 'Digit9', 'Digit0',
    # Second row
    'KeyQ', 'KeyW', 'KeyE', 'KeyR', 'KeyT', 'KeyY', 'KeyU', 'KeyI', 'KeyO', 'KeyP',
    # Third row
    'KeyA', 'KeyS', 'KeyD', 'KeyF', 'KeyG', 'KeyH', 'KeyJ', 'KeyK', 'KeyL',
    # Fourth row
    'KeyZ', 'KeyX', 'KeyC', 'KeyV', 'KeyB', 'KeyN', 'KeyM'
]

def main():
    """Main function to map audio files to keyboard keys"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    web_audio_dir = os.path.join(script_dir, 'web', 'audio')
    audio_dir = os.path.join(script_dir, 'audio')
    mapping_file = os.path.join(script_dir, 'keyboard_mapping.json')
    
    # Create directories if they don't exist
    os.makedirs(web_audio_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # Find all audio files
    audio_files = []
    for ext in ['*.wav', '*.mp3', '*.ogg']:
        audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))
    
    # Load existing mapping if available
    keyboard_mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r') as f:
                keyboard_mapping = json.load(f)
            print(f"Loaded existing mapping with {len(keyboard_mapping)} entries")
        except Exception as e:
            print(f"Error loading mapping file: {e}")
    
    # Display menu
    while True:
        print("\n=== Keyboard Mapping Tool ===")
        print("1. Auto-map audio files to keys")
        print("2. Manually map an audio file to a key")
        print("3. Remove a mapping")
        print("4. Show current mappings")
        print("5. Save mappings")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ")
        
        if choice == '1':
            auto_map(audio_files, keyboard_mapping, web_audio_dir)
        elif choice == '2':
            manual_map(audio_files, keyboard_mapping, web_audio_dir)
        elif choice == '3':
            remove_mapping(keyboard_mapping)
        elif choice == '4':
            show_mappings(keyboard_mapping)
        elif choice == '5':
            save_mappings(keyboard_mapping, mapping_file)
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid choice!")

def auto_map(audio_files, keyboard_mapping, web_audio_dir):
    """Automatically map audio files to keyboard keys"""
    # Clear existing mappings if user wants
    clear = input("Clear existing mappings? (y/n): ").lower() == 'y'
    if clear:
        keyboard_mapping.clear()
    
    # Map each audio file to an available key
    count = 0
    used_keys = set(keyboard_mapping.keys())
    
    for audio_file in audio_files:
        # Find an available key
        available_keys = [k for k in KEYBOARD_KEYS if k not in used_keys]
        if not available_keys:
            print("No more keys available!")
            break
        
        key = available_keys[0]
        used_keys.add(key)
        
        # Copy the file to web audio directory if needed
        filename = os.path.basename(audio_file)
        web_path = os.path.join(web_audio_dir, filename)
        if not os.path.exists(web_path):
            shutil.copy2(audio_file, web_path)
        
        # Add mapping
        keyboard_mapping[key] = f"audio/{filename}"
        count += 1
    
    print(f"Auto-mapped {count} audio files to keys")

def manual_map(audio_files, keyboard_mapping, web_audio_dir):
    """Manually map an audio file to a key"""
    # Show available audio files
    print("\nAvailable audio files:")
    for i, audio_file in enumerate(audio_files):
        print(f"{i+1}. {os.path.basename(audio_file)}")
    
    try:
        file_idx = int(input("\nEnter file number: ")) - 1
        if file_idx < 0 or file_idx >= len(audio_files):
            print("Invalid file number")
            return
        
        audio_file = audio_files[file_idx]
        filename = os.path.basename(audio_file)
        
        # Show available keys
        print("\nAvailable keys:")
        for i, key in enumerate(KEYBOARD_KEYS):
            print(f"{key} - {'Mapped' if key in keyboard_mapping else 'Available'}")
        
        key = input("\nEnter key (e.g. KeyA, Digit1): ")
        if key not in KEYBOARD_KEYS:
            print(f"Invalid key: {key}")
            return
        
        # Copy the file to web audio directory if needed
        web_path = os.path.join(web_audio_dir, filename)
        if not os.path.exists(web_path):
            shutil.copy2(audio_file, web_path)
        
        # Add mapping
        keyboard_mapping[key] = f"audio/{filename}"
        print(f"Mapped {key} to {filename}")
    
    except ValueError:
        print("Invalid input")
    except Exception as e:
        print(f"Error: {e}")

def remove_mapping(keyboard_mapping):
    """Remove a mapping"""
    # Show existing mappings
    if not keyboard_mapping:
        print("No mappings to remove")
        return
    
    print("\nCurrent mappings:")
    for key, file in keyboard_mapping.items():
        print(f"{key} -> {os.path.basename(file)}")
    
    key = input("\nEnter key to remove: ")
    if key in keyboard_mapping:
        del keyboard_mapping[key]
        print(f"Removed mapping for {key}")
    else:
        print(f"No mapping found for {key}")

def show_mappings(keyboard_mapping):
    """Show current mappings"""
    if not keyboard_mapping:
        print("No mappings defined")
        return
    
    print("\nCurrent mappings:")
    for key, file in sorted(keyboard_mapping.items()):
        print(f"{key} -> {os.path.basename(file)}")

def save_mappings(keyboard_mapping, mapping_file):
    """Save mappings to file"""
    try:
        with open(mapping_file, 'w') as f:
            json.dump(keyboard_mapping, f, indent=2)
        print(f"Saved {len(keyboard_mapping)} mappings to {mapping_file}")
    except Exception as e:
        print(f"Error saving mapping file: {e}")

if __name__ == "__main__":
    main()
