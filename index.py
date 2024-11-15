import subprocess
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, find_peaks
import argparse
import os

def separate_vocals(audio_file):
    try:
        # Run the Demucs command to separate vocals
        result = subprocess.run(
            ['demucs', '--two-stems=vocals', audio_file],
            check=True,
            text=True,
            capture_output=True
        )
        
        print("Output:\n", result.stdout)
        print("Errors (if any):\n", result.stderr)
        
        # Construct path to the separated vocals file
        base_name = os.path.basename(audio_file)
        file_name_without_extension = os.path.splitext(base_name)[0]
        separated_audio_path = os.path.join(os.getcwd(), 'separated', 'htdemucs', file_name_without_extension, 'vocals.wav')
        
        return separated_audio_path
        
    except subprocess.CalledProcessError as e:
        print("An error occurred while running Demucs:")
        print(e.stderr)
        return None

def process_vocals(vocal_audio_file):
    # Load the audio file using librosa
    audio, sr = librosa.load(vocal_audio_file, sr=None)
    
    # Compute the RMS energy of the audio signal
    rms = librosa.feature.rms(y=audio)[0]

    # Step 2: Smooth the RMS values using the Savitzky-Golay filter
    smoothed_rms = savgol_filter(rms, window_length=70, polyorder=4)  # Adjust window_length for smoothing

    # Step 3: Find peaks and troughs in the smoothed RMS signal
    smoothed_peaks, _ = find_peaks(smoothed_rms, height=0.1)
    smoothed_troughs, _ = find_peaks(-smoothed_rms, height=0.1)

    # Convert frame indices to time in seconds
    times = librosa.frames_to_time(np.arange(len(smoothed_rms)), sr=sr)

    # Plot only smoothed peaks and troughs
    plt.figure(figsize=(10, 6))
    plt.plot(times, smoothed_rms, label='Smoothed RMS', linestyle='--')
    plt.plot(times[smoothed_peaks], smoothed_rms[smoothed_peaks], 'r^', label='Smoothed Peaks')
    plt.plot(times[smoothed_troughs], smoothed_rms[smoothed_troughs], 'bv', label='Smoothed Troughs')
    
    plt.title("Smoothed RMS Energy with Peaks and Troughs")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Smoothed RMS energy")
    plt.legend()
    plt.show()

    return smoothed_rms, smoothed_peaks, smoothed_troughs, times

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Separate vocals from audio, process and visualize RMS peaks/troughs.")
    parser.add_argument(
        'audio_file', 
        type=str, 
        help="Path to the input audio file."
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Step 1: Separate vocals
    separated_audio_file = separate_vocals(args.audio_file)
    
    if separated_audio_file:
        print(f"Separated vocals saved at: {separated_audio_file}")
        
        # Step 2: Process vocals and visualize only smoothed peaks/troughs
        smoothed_rms, smoothed_peaks, smoothed_troughs, times = process_vocals(separated_audio_file)
        
        # Output the results
        print("Smoothed RMS:", smoothed_rms)
        print("Smoothed Peaks:", smoothed_peaks)
        print("Smoothed Troughs:", smoothed_troughs)
        print("Times (seconds):", times)
    else:
        print("Error in separating vocals.")

if __name__ == "__main__":
    main()
