import os
import asyncio
from datetime import timedelta
import tempfile
import edge_tts
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator, MyMemoryTranslator
from pydub import AudioSegment

def format_timestamp(seconds: float):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

async def generate_tts(text: str, voice: str, output_path: str):
    """Generate audio for a single sentence using edge-tts"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def denoise_audio(input_path: str, output_path: str):
    """Use FFmpeg to reduce background noise from the original audio before transcription."""
    print("Denoising audio for cleaner transcription...")
    # Using afftdn (Fast Fourier Transform Denoise) - a great free built-in FFmpeg filter
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", "afftdn=nr=12:nt=w:om=o", 
        "-ar", "16000", "-ac", "1", # Downsample for Whisper optimization
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Denoising failed: {e}")
        return False

def change_audio_speed(input_path: str, output_path: str, speed: float):
    """Use FFmpeg to change the speed of an audio segment without changing pitch."""
    # Speed must be between 0.5 and 2.0 for atempo
    speed = max(0.5, min(2.0, speed))
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", f"atempo={speed}",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Speed adjustment failed: {e}")
        return False

def process_ai_translation(video_path: str, target_language: str, output_dir: str, quality: str = "Fast"):
    """
    End-to-end AI pipeline for video dubbing.
    target_language: "English" or "Hindi"
    quality: "Fast" (Turbo) or "Ultra" (Large-v3 + Beam Search)
    Returns: (generated_audio_path, generated_srt_path)
    """
    model_name = "turbo" if quality == "Fast" else "large-v3"
    beam_size = 1 if quality == "Fast" else 5
    
    print(f"Starting {quality} Accuracy Pipeline using '{model_name}' model...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Pre-processing: Denoise audio
    temp_audio = os.path.join(output_dir, "denoised_temp.wav")
    if denoise_audio(video_path, temp_audio):
        transcribe_source = temp_audio
    else:
        transcribe_source = video_path

    print(f"Loading Whisper model ({model_name})...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    
    print("Extracting audio, transcribing, and converting to base English...")
    # condition_on_previous_text=False prevents loops.
    # beam_size=5 (in Ultra) explores more possibilities for much higher accuracy.
    segments_generator, info = model.transcribe(
        transcribe_source, 
        task="translate", 
        condition_on_previous_text=False, 
        vad_filter=True,
        beam_size=beam_size
    )
    all_segments = list(segments_generator)
    
    # Cleanup temp denoised audio
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    
    # Deduplication Step: Remove consecutive identical segments (common Whisper hallucination)
    segments = []
    last_text = None
    for s in all_segments:
        current_text = s.text.strip().lower()
        if current_text != last_text:
            segments.append(s)
            last_text = current_text
        else:
            print(f"Skipping repetitive segment: {s.text.strip()}")
            # We skip the TTS but the timeline will stay silent there.
    
    print(f"Refined {len(segments)} segments after deduplication (from {len(all_segments)} original).")

    # Prepare text translation if needed
    translator = None
    if target_language == "Hindi":
        # Using GoogleTranslator but with improved batching for better grammar
        translator = GoogleTranslator(source='en', target='hi')
        
    voice = "en-US-ChristopherNeural" if target_language == "English" else "hi-IN-SwaraNeural"
    
    srt_content = ""
    combined_audio = AudioSegment.silent(duration=0)
    current_time_ms = 0
    temp_dir = tempfile.mkdtemp()
    
    print(f"Detected {len(segments)} audio segments.")
    
    # 1. Translate all text in one batch if possible to maintain context
    raw_texts = [segment.text.strip() for segment in segments if segment.text.strip()]
    translated_texts = list(raw_texts)
    
    if not raw_texts:
        print("⚠️ Warning: No speech detected in video. Generating empty assets.")
        # Create a single "silence" entry so FFmpeg doesn't crash on an empty file
        srt_content = "1\n00:00:00,000 --> 00:00:01,000\n[Silence]\n\n"
        translated_texts = ["[Silence]"]
    elif target_language == "Hindi" and translator:
        try:
            print(f"Translating {len(raw_texts)} segments to Hindi (Contextual Batching)...")
            
            # Using translate_batch which is more robust than manual joining
            translated_texts = translator.translate_batch(raw_texts)
            
            if len(translated_texts) != len(raw_texts):
                print(f"⚠️ Batch size mismatch ({len(translated_texts)} vs {len(raw_texts)}).")
                # Fallback to line by line if somehow the list length changed (unlikely with translate_batch)
                translated_texts = [translator.translate(t) for t in raw_texts]
            else:
                print("✅ Batch translation successful.")
                
        except Exception as e:
            print(f"⚠️ Batch translation failed: {e}. Falling back to line-by-line.")
            translated_texts = []
            for t in raw_texts:
                try:
                    translated_texts.append(translator.translate(t))
                except:
                    translated_texts.append(t)
    
    # Ensure translated_texts matches length of segments (if some segments were empty space)
    final_text_map = []
    text_ptr = 0
    for segment in segments:
        if segment.text.strip():
            final_text_map.append(translated_texts[text_ptr] if text_ptr < len(translated_texts) else segment.text.strip())
            text_ptr += 1
        else:
            final_text_map.append("")

    for idx, (segment, text) in enumerate(zip(segments, final_text_map), start=1):
        if not text: continue
        
        # 2. Build SRT entry
        start_time = segment.start
        end_time = segment.end
        srt_content += f"{idx}\n"
        srt_content += f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n"
        srt_content += f"{text}\n\n"
        
        # 3. Generate Audio for this segment
        segment_audio_path = os.path.join(temp_dir, f"seg_{idx}.mp3")
        try:
            asyncio.run(generate_tts(text, voice, segment_audio_path))
            
            # 4. Smart-Sync: Stretch/Compress audio to fit exactly in the time slot
            # This prevents audio from drifting or overlapping.
            original_duration_s = end_time - start_time
            spoken_audio = AudioSegment.from_file(segment_audio_path)
            generated_duration_s = len(spoken_audio) / 1000.0
            
            # Calculate required speed factor
            # If target is 2s and we have 2.5s, speed = 1.25
            speed_factor = generated_duration_s / original_duration_s
            
            # If the difference is significant (>5%), adjust the speed
            if abs(speed_factor - 1.0) > 0.05:
                synced_path = os.path.join(temp_dir, f"synced_{idx}.mp3")
                if change_audio_speed(segment_audio_path, synced_path, speed_factor):
                    spoken_audio = AudioSegment.from_file(synced_path)
            
            # 5. Mix generated audio onto timeline
            target_start_ms = int(start_time * 1000)
            
            # Force timeline to match start_time exactly (removes cumulative drift)
            if target_start_ms > current_time_ms:
                silence_duration = target_start_ms - current_time_ms
                combined_audio += AudioSegment.silent(duration=silence_duration)
                current_time_ms += silence_duration
            elif target_start_ms < current_time_ms:
                # If we are ahead (unlikely with sync but possible), trim the silence
                combined_audio = combined_audio[:target_start_ms]
                current_time_ms = target_start_ms
                
            combined_audio += spoken_audio
            current_time_ms += len(spoken_audio)
            
        except Exception as e:
            print(f"Failed to generate TTS for segment {idx}: {e}")
            
    # Save outputs
    final_audio_path = os.path.join(output_dir, f"ai_generated_{target_language}.wav")
    final_srt_path = os.path.join(output_dir, f"ai_generated_{target_language}.srt")
    
    combined_audio.export(final_audio_path, format="wav")
    with open(final_srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
        
    print(f"✅ AI Generation Complete! Audio and Subtitles saved in {output_dir}")
    return final_audio_path, final_srt_path

if __name__ == "__main__":
    # Test script locally with the sample video
    sample_vid = "assets/kannada_sample.mp4"
    if os.path.exists(sample_vid):
        process_ai_translation(sample_vid, "Hindi", "assets")
