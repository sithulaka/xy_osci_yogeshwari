import numpy as np
from scipy.io import wavfile
import svgpathtools as svgpath
import os
import glob

def generate_oscilloscope_audio(svg_file, output_wav, sample_rate=44100, duration=10.0, speed_factor=5.0, repetitions=10):
    """
    Generate audio that will draw the SVG on an XY oscilloscope
    
    Parameters:
    svg_file -- Path to the SVG file
    output_wav -- Path to save the audio file
    sample_rate -- Audio sample rate in Hz
    duration -- Length of the audio in seconds
    speed_factor -- Higher values make drawing faster
    repetitions -- Number of times to draw the complete image
    """
    print(f"Parsing SVG file: {svg_file}")
    
    # Parse the SVG file
    paths, _ = svgpath.svg2paths(svg_file)
    
    # Sample points from all paths
    all_points = []
    for path in paths:
        # Determine number of points based on path length
        num_samples = max(100, int(path.length() * 0.2))
        
        for t in np.linspace(0, 1, num_samples):
            point = path.point(t)
            all_points.append((point.real, point.imag))
    
    print(f"Extracted {len(all_points)} points from SVG")
    
    # Normalize points to [-1, 1] range for audio
    x_values = [p[0] for p in all_points]
    y_values = [p[1] for p in all_points]
    
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    
    normalized_points = []
    for x, y in all_points:
        # Normalize to [-1, 1] range
        x_norm = 2 * (x - x_min) / (x_max - x_min) - 1
        y_norm = 2 * (y - y_min) / (y_max - y_min) - 1
        # Invert Y axis to match SVG coordinate system
        normalized_points.append((x_norm, -y_norm))
    
    # Generate audio samples with interpolation for smoothness
    num_samples = int(sample_rate * duration)
    x_channel = np.zeros(num_samples)
    y_channel = np.zeros(num_samples)
    
    total_points = len(normalized_points)
    
    # Add smooth transitions between repetitions
    transition_points = int(total_points * 0.05)  # 5% of points for transition
    
    for i in range(num_samples):
        # Calculate which repetition we're in
        rep_duration = duration / repetitions
        rep_samples = num_samples / repetitions
        current_rep = int(i / rep_samples)
        
        # Calculate position within current repetition (0 to 1)
        pos_in_rep = (i % rep_samples) / rep_samples
        
        # Apply speed factor (faster = cover more points in the same time)
        point_position = (pos_in_rep * speed_factor * total_points) % total_points
        
        # Calculate which two points we should be between
        idx1 = int(point_position) % total_points
        idx2 = (idx1 + 1) % total_points
        
        # Interpolation factor
        alpha = point_position - int(point_position)
        
        # Interpolate between the two points for smoothness
        x_channel[i] = (1 - alpha) * normalized_points[idx1][0] + alpha * normalized_points[idx2][0]
        y_channel[i] = (1 - alpha) * normalized_points[idx1][1] + alpha * normalized_points[idx2][1]
    
    # Create stereo audio (left = X, right = Y)
    audio_data = np.column_stack((x_channel, y_channel))
    
    # Optional: Add a small amount of noise to reduce aliasing artifacts
    noise = np.random.normal(0, 0.001, audio_data.shape)
    audio_data = audio_data + noise
    
    # Ensure audio stays within [-1, 1] range
    audio_data = np.clip(audio_data, -1.0, 1.0)
    
    # Save as WAV file
    wavfile.write(output_wav, sample_rate, audio_data.astype(np.float32))
    print(f"Audio saved to {output_wav}")
    print(f"Drawing speed: {speed_factor}x, Repetitions: {repetitions}")

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output directories
    svg_dir = os.path.join(script_dir, "svg")
    audio_dir = os.path.join(script_dir, "audio")
    
    # Create directories if they don't exist
    os.makedirs(svg_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # Get all SVG files
    svg_files = glob.glob(os.path.join(svg_dir, "*.svg"))
    
    if not svg_files:
        print(f"No SVG files found in {svg_dir}")
    else:
        print(f"Found {len(svg_files)} SVG files to process")
        
        # Process each SVG file
        for svg_file in svg_files:
            # Get the filename without the directory and extension
            base_name = os.path.basename(svg_file)
            name_without_ext = os.path.splitext(base_name)[0]
            
            # Output WAV file path
            output_wav = os.path.join(audio_dir, f"{name_without_ext}.wav")
            
            print(f"\nProcessing: {base_name}")
            
            # Generate audio for this SVG
            generate_oscilloscope_audio(
                svg_file, 
                output_wav, 
                duration=15.0,       # 15 seconds of audio
                speed_factor=3.0,    # Draw 3x faster than original
                repetitions=10       # Draw the image 10 times
            )
    
    print("\nAll SVG files processed!")
    print("Instructions:")
    print("1. Open the oscilloscope.js in your browser")
    print("2. Set the oscilloscope to XY mode (swap XY checkbox if needed)")
    print("3. Play any of the generated audio files in the ./audio folder")
