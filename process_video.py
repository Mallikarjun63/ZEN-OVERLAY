import argparse
import subprocess
import os
import sys

def process_video(
    input_video: str,
    input_english_audio: str,
    input_subtitles: str,
    output_video: str,
    kannada_volume_lufs: float = -21.0,
    english_speed: float = 0.95
):
    """
    Overlays English audio on top of Kannada (original) video audio,
    applies EQ, speed changes, and muxes in subtitles.
    """
    
    # We no longer need to check inputs via ffmpeg-python.
    # We just trust the paths passed in and build the string.
    for p in [input_video, input_english_audio, input_subtitles]:
        if not os.path.exists(p):
            print(f"Error loading input, file not found: {p}")
            sys.exit(1)

    # Build the complex filtergraph string
    eq_filter = 'c0 f=1500 w=1000 g=-6 t=0|c1 f=1500 w=1000 g=-6 t=0'
    filter_complex = (
        f"[0:a]loudnorm=I={kannada_volume_lufs}:LRA=11:TP=-1.5,"
        f"anequalizer={eq_filter}[ducked_bg]; "
    )
    
    if english_speed != 1.0:
        filter_complex += f"[1:a]atempo={english_speed},"
    else:
        filter_complex += f"[1:a]"
        
    filter_complex += (
        f"loudnorm=I=-14.0:LRA=11:TP=-1.0[norm_eng]; "
        f"[ducked_bg][norm_eng]amix=inputs=2:normalize=0[a_out]"
    )

    # Ensure output is .mkv for proper subtitle support
    if not output_video.lower().endswith('.mkv'):
        print("Note: Output changed to .mkv to support subtitles properly on macOS.")
        output_video = output_video.rsplit('.', 1)[0] + '.mkv'
    
    # 6. Output Map and Run
    print(f"Starting processing... Output will be saved to: {output_video}")
    print("This may take some time depending on the video length.")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", input_english_audio,
        "-i", input_subtitles,
        "-filter_complex", filter_complex,
        "-map", "0:v:0",    # Map original video stream
        "-map", "[a_out]",  # Map mixed audio stream
        "-map", "2:s:0",    # Map subtitle stream from 3rd input
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-c:s", "srt",
        "-disposition:s:0", "default", # Force subtitle on by default
        output_video
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\nProcessing complete! 🎉")
    except subprocess.CalledProcessError as e:
        print("\nFFmpeg error.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Netflix-style audio overlays.")
    parser.add_argument("--video", required=True, help="Path to original video (with Kannada audio)")
    parser.add_argument("--audio", required=True, help="Path to English audio track")
    parser.add_argument("--subtitles", required=True, help="Path to English subtitle file (.srt or .vtt)")
    parser.add_argument("--output", default="output_final.mp4", help="Output file path")
    parser.add_argument("--lufs", type=float, default=-21.0, help="Target LUFS for background Kannada audio (default: -21)")
    parser.add_argument("--speed", type=float, default=0.95, help="Speed adjustment for English audio (default: 0.95)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    if not os.path.exists(args.audio):
        print(f"Error: Audio file not found: {args.audio}")
        sys.exit(1)
    if not os.path.exists(args.subtitles):
        print(f"Error: Subtitle file not found: {args.subtitles}")
        sys.exit(1)
        
    process_video(
        input_video=args.video,
        input_english_audio=args.audio,
        input_subtitles=args.subtitles,
        output_video=args.output,
        kannada_volume_lufs=args.lufs,
        english_speed=args.speed
    )
