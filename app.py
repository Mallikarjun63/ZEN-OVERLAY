import gradio as gr
import subprocess
import os
import shutil
from ai_translator import process_ai_translation

def run_translation(kannada_video_path, english_audio_path, subtitles_path, lufs, speed):
    if not kannada_video_path or not english_audio_path or not subtitles_path:
        return None, "Error: Please upload a Video, an Audio track, and a Subtitle file."
        
    output_path = "assets/user_final_mix.mkv"
    
    # Run our script via subprocess
    cmd = [
        "python", "process_video.py",
        "--video", kannada_video_path,
        "--audio", english_audio_path,
        "--subtitles", subtitles_path,
        "--output", output_path,
        "--lufs", str(lufs),
        "--speed", str(speed)
    ]
    
    try:
        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path, "✅ Processing Complete! Your video is ready below."
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ FFmpeg Error:\n{e.stderr}"
        return None, error_msg

def run_ai_translation(video_path, target_language, quality, lufs, speed):
    if not video_path:
        return None, "Error: Please upload a Video."
        
    output_dir = "assets/ai_temp"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. Run AI Extraction & Generation
        generated_audio, generated_srt = process_ai_translation(video_path, target_language, output_dir, quality=quality)
        
        # 2. Run the mixing pipeline using the generated assets
        final_output = f"assets/final_ai_{target_language}.mkv"
        
        cmd = [
            "python", "process_video.py",
            "--video", video_path,
            "--audio", generated_audio,
            "--subtitles", generated_srt,
            "--output", final_output,
            "--lufs", str(lufs),
            "--speed", str(speed)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Cleanup temp parsing files
        shutil.rmtree(output_dir, ignore_errors=True)
        
        return final_output, f"✅ AI Pipeline Complete! Successfully translated to {target_language}."
        
    except Exception as e:
        return None, f"❌ Pipeline Error: {str(e)}"

# Gradio Interface
with gr.Blocks(title="Netflix-Style Audio Overlay") as demo:
    gr.Markdown("# 🎬 Audio Dubbing & Subtitling Pipeline")
    
    with gr.Tabs():
        
        # TAB 1: FULLY AUTOMATED AI
        with gr.Tab("🤖 Auto AI Translator"):
            gr.Markdown("Upload **just** your Kannada video. The AI will automatically transcribe, translate, generate new voice acting, and mix it into a Netflix-style documentary.")
            with gr.Row():
                with gr.Column():
                    ai_video_in = gr.Video(label="Original Video", source="upload")
                    ai_lang_in = gr.Radio(["English", "Hindi"], label="Target Language", value="English")
                    
                    gr.Markdown("### Fine-Tuning")
                    ai_quality_in = gr.Dropdown(["Fast", "Ultra"], label="AI Quality (Best of Best)", value="Fast", info="Ultra uses denoising and beam search for maximum accuracy.")
                    ai_lufs_slider = gr.Slider(-30.0, -10.0, value=-21.0, step=1.0, label="Background Volume (LUFS)")
                    ai_speed_slider = gr.Slider(0.8, 1.2, value=0.95, step=0.01, label="Voice Speed")
                    ai_btn = gr.Button("🚀 Start AI Pipeline", variant="primary")
                
                with gr.Column():
                    ai_status = gr.Textbox(label="Status", interactive=False)
                    ai_video_out = gr.Video(label="Final Output Video", interactive=False)
            
            ai_btn.click(
                fn=run_ai_translation,
                inputs=[ai_video_in, ai_lang_in, ai_quality_in, ai_lufs_slider, ai_speed_slider],
                outputs=[ai_video_out, ai_status]
            )

        # TAB 2: MANUAL MIXING
        with gr.Tab("🎛️ Manual Mixer"):
            gr.Markdown("Already have your Translation Audio and SRT file? Drop them here to mix them perfectly.")
            with gr.Row():
                with gr.Column():
                    man_video_in = gr.Video(label="Original Video", source="upload")
                    man_audio_in = gr.Audio(label="Translated Audio Track", type="filepath", source="upload")
                    man_sub_in = gr.File(label="Translated Subtitles (.srt)", file_types=[".srt", ".vtt"])
                    
                    man_lufs_slider = gr.Slider(-30.0, -10.0, value=-21.0, step=1.0, label="Background Volume (LUFS)")
                    man_speed_slider = gr.Slider(0.8, 1.2, value=0.95, step=0.01, label="Voice Speed")
                    man_btn = gr.Button("🎛️ Process Mix", variant="secondary")
                    
                with gr.Column():
                    man_status = gr.Textbox(label="Status", interactive=False)
                    man_video_out = gr.Video(label="Final Output Box", interactive=False)
                    
            man_btn.click(
                fn=run_translation,
                inputs=[man_video_in, man_audio_in, man_sub_in, man_lufs_slider, man_speed_slider],
                outputs=[man_video_out, man_status]
            )

if __name__ == "__main__":
    # Ensure assets directory exists for saving dummy
    os.makedirs("assets", exist_ok=True)
    print("Starting Web UI... Check your browser!")
    demo.launch(server_name="127.0.0.1", server_port=7860, show_error=True)
