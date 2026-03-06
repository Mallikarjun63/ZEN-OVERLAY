# 🎬 ZEN-OVERLAY: AI-Powered Video Dubbing & Audio Overlay

ZEN-OVERLAY is a professional-grade automated pipeline designed to translate and dub videos (specializing in Kannada to English/Hindi) with a "Netflix-style" documentary feel. It features background audio preservation, AI noise reduction, and smart synchronization.

---

## 🚀 Key Features

*   **🤖 Full AI Automation**: Upload a video and get a fully dubbed and subtitled version in minutes.
*   **🎙️ Smart-Sync Technology**: Automatically time-stretches/compresses generated AI voices to match the original speaker's timing perfectly.
*   **🌐 High-Accuracy Translation**: Uses **Whisper Turbo/Large-v3** for transcription and **Google Batch Translation** for grammatically correct Hindi.
*   **🔊 Premium Audio Overlay**: 
    *   Preserves original background audio (lowered to -21 LUFS).
    *   Applies a mid-frequency EQ cut to the background track so the new voice sits "behind" the mix.
*   **✨ Ultra-Accuracy Mode**: Includes AI-powered audio denoising and advanced beam-search decoding for maximum precision.
*   **🎥 Hardcoded Subtitles**: Automatically generates and burns in SRT subtitles for better social media retention.

---

## 🛠️ Technical Stack

- **Transcription/Translation**: [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (Turbo & Large-v3)
- **Text-to-Speech**: [Edge-TTS](https://github.com/rany2/edge-tts) (Microsoft Neural Voices)
- **Audio Processing**: [FFmpeg](https://ffmpeg.org/) & [Pydub](https://github.com/jiaaro/pydub)
- **UI Framework**: [Gradio](https://gradio.app/)
- **Translation Engine**: [Deep-Translator](https://github.com/nidhaloff/deep-translator)

---

## 📥 Installation & Setup

### 1. Prerequisites
Ensure you have **FFmpeg** installed on your system:
```bash
# On Mac
brew install ffmpeg
```

### 2. Clone the Repository
```bash
git clone https://github.com/Mallikarjun63/ZEN-OVERLAY.git
cd ZEN-OVERLAY
```

### 3. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:7860`.

---

## 📖 Usage Guide

1.  **Auto AI Translator**: Drop your Kannada video file, select "Hindi" or "English", and hit **Start AI Pipeline**.
2.  **Fine-Tuning**:
    *   **Quality**: Use "Fast" for quick results or "Ultra" for the best possible accuracy.
    *   **Background Volume**: Control how loud the original voice stays in the background.
    *   **Voice Speed**: Adjust the base speed of the AI narrator.
3.  **Manual Mixer**: If you already have a voiceover and an SRT file, use this tab to mix them with professional Netflix-style settings.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
MIT License - created by Mallikarjun63
