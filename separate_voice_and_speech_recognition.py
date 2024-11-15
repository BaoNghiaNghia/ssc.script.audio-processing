import subprocess
import argparse
import speech_recognition as sr
from pydub import AudioSegment
import srt
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

def transcribe_audio(audio_file):
    # Initialize recognizer
    recognizer = sr.Recognizer()
    transcripts = []
    
    # Load audio file
    audio = AudioSegment.from_wav(audio_file)  # Demucs outputs .wav files

    # Split audio into smaller chunks for recognition
    chunk_length = 60 * 1000  # 60 seconds per chunk
    for i in range(0, len(audio), chunk_length):
        chunk = audio[i:i+chunk_length]
        chunk_file = f"chunk_{i // chunk_length}.wav"
        chunk.export(chunk_file, format="wav")
        
        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                print(f"Transcribed text for chunk {i // chunk_length}: {text}")
                transcripts.append(text)
            except sr.UnknownValueError:
                print(f"No recognizable speech in chunk {i // chunk_length}")
                transcripts.append("")  # No speech detected
            except sr.RequestError as e:
                print(f"API error for chunk {i // chunk_length}: {e}")
                transcripts.append("")

        # Clean up temporary chunk file
        os.remove(chunk_file)

    return transcripts

def create_srt(transcripts, output_srt):
    # Assuming each transcript corresponds to 60 seconds
    start_time = 0  # Start time in seconds
    srt_items = []

    for idx, text in enumerate(transcripts):
        if text.strip():  # Only create entries for non-empty texts
            end_time = start_time + 60  # End time (next 60 seconds)
            start_time_code = start_time // 60
            end_time_code = end_time // 60
            
            subtitle = srt.Subtitle(index=idx + 1,
                                    start=srt.timedelta(seconds=start_time),
                                    end=srt.timedelta(seconds=end_time),
                                    content=text)
            srt_items.append(subtitle)
            start_time = end_time

    # Write to output SRT file
    with open(output_srt, 'w') as f:
        f.write(srt.compose(srt_items))

    if srt_items:
        print(f"SRT file created successfully with {len(srt_items)} entries.")
    else:
        print("SRT file was created but is empty due to no transcriptions.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Separate vocals from audio and create synchronized SRT file.")
    parser.add_argument(
        'audio_file', 
        type=str, 
        help="Path to the input audio file."
    )
    parser.add_argument(
        'output_srt', 
        type=str, 
        help="Path for the output SRT file."
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Step 1: Separate vocals
    separated_audio_file = separate_vocals(args.audio_file)
    
    if separated_audio_file:
        print(f"Separated vocals saved at: {separated_audio_file}")
        
        # Step 2: Transcribe the separated vocals
        transcripts = transcribe_audio(separated_audio_file)
        
        # Step 3: Create SRT file if there are valid transcripts
        if any(transcripts):  # Only proceed if there are valid non-empty transcriptions
            create_srt(transcripts, args.output_srt)
        else:
            print("No valid transcriptions were generated. Check audio quality or transcription service.")
    else:
        print("Error in separating vocals. SRT file not created.")

if __name__ == "__main__":
    main()
