import os
import subprocess
from aeneas.executetask import ExecuteTask
from aeneas.task import Task
import pysubs2
import re
import shutil

def spleeter_separate(audio_file, output_dir="output"):
    """Uses Spleeter to isolate vocals and instrumentals."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    command = f"spleeter separate -i {audio_file} -p spleeter:2stems -o {output_dir}"
    subprocess.call(command, shell=True)
    vocals_path = os.path.join(output_dir, audio_file.split('.')[0], "vocals.wav")
    return vocals_path

def generate_timed_lyrics(vocals_path, lyrics_path, output_srt):
    """Uses Aeneas to generate a synchronized SRT file from lyrics and isolated vocals."""
    config_string = "task_language=eng|os_task_file_format=srt|is_text_type=plain"
    task = Task(config_string=config_string)
    task.audio_file_path_absolute = vocals_path
    task.text_file_path_absolute = lyrics_path
    task.sync_map_file_path_absolute = output_srt
    ExecuteTask(task).execute()
    task.output_sync_map_file()
    print(f"Generated synchronized lyrics: {output_srt}")

def split_syllables(text):
    """Simple function to split text into syllables based on whitespace."""
    return re.findall(r'\w+|\s+|[^\w\s]', text)

def apply_karaoke_effects(line, syllables, start_ms, end_ms):
    """Apply karaoke effects by splitting the line into timed syllables."""
    duration = end_ms - start_ms
    syllable_durations = duration // len(syllables)
    formatted_text = ""
    current_time = start_ms

    # Apply a color fade effect for each syllable
    for syllable in syllables:
        syllable_text = syllable.strip()
        if syllable_text:
            formatted_text += f"{{\\k{syllable_durations // 10}}}{syllable_text}"
        current_time += syllable_durations

    return formatted_text

def process_srt_to_ass(srt_path, output_ass_path):
    """Convert SRT to ASS with karaoke effects applied."""
    subs = pysubs2.load(srt_path, encoding="utf-8")
    subs.info.update({"PlayResX": 1280, "PlayResY": 720})  # Resolution for ASS style

    # Define a basic style for karaoke
    style = pysubs2.Style("Karaoke",
                          fontname="Arial",
                          fontsize=48,
                          primarycolor="&H00FFFFFF",  # White text
                          outlinecolor="&H00000000",  # Black outline
                          backcolor="&H00000000",     # Transparent background
                          outline=1.5,
                          shadow=0,
                          alignment=pysubs2.ALIGN_CENTERED,
                          bold=True)
    subs.styles["Karaoke"] = style

    for line in subs:
        start_ms = line.start
        end_ms = line.end
        syllables = split_syllables(line.text)

        # Convert the line with karaoke effects applied
        karaoke_text = apply_karaoke_effects(line, syllables, start_ms, end_ms)
        
        # Update the line with the new effects and style
        line.text = karaoke_text
        line.style = "Karaoke"

    # Save the new file in ASS format
    subs.save(output_ass_path)
    print(f"Karaoke ASS file created: {output_ass_path}")

def main(audio_file, lyrics_file, output_dir="output"):
    """Main function to perform all steps and output a karaoke .ass file."""
    print("Starting auto karaoke process...")
    
    # Step 1: Use Spleeter to isolate vocals
    print("Step 1: Isolating vocals using Spleeter...")
    vocals_path = spleeter_separate(audio_file, output_dir)
    print(f"Vocals isolated: {vocals_path}")

    # Step 2: Generate timed lyrics using Aeneas
    print("Step 2: Generating timed lyrics using Aeneas...")
    output_srt = os.path.join(output_dir, "timed_lyrics.srt")
    generate_timed_lyrics(vocals_path, lyrics_file, output_srt)
    
    # Step 3: Convert SRT to ASS with karaoke effects
    print("Step 3: Applying karaoke effects and converting to ASS format...")
    output_ass = os.path.join(output_dir, "karaoke_output.ass")
    process_srt_to_ass(output_srt, output_ass)
    
    print("Auto karaoke process complete!")
    print(f"Karaoke ASS file created at {output_ass}")

# Example usage:
# Replace 'song.mp3' and 'lyrics.txt' with your own audio file and lyrics file paths.
if __name__ == "__main__":
    audio_file = "song.mp3"  # Path to your song file
    lyrics_file = "lyrics.txt"  # Path to your lyrics file
    main(audio_file, lyrics_file)
