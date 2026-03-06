import os
from gtts import gTTS

def create_sample_files():
    # 1. Dummy Subtitles
    srt_content = """1
00:00:00,000 --> 00:00:03,000
This is an English translation test.

2
00:00:03,000 --> 00:00:06,000
We are testing the Netflix overlay style.
"""
    with open("assets/sample.srt", "w") as f:
        f.write(srt_content)

    # 2. Generate Dummy English Audio (6 seconds)
    tts = gTTS(text="This is an English translation test. We are testing the Netflix overlay style.", lang='en')
    tts.save("assets/tmp_eng.mp3")

    # 3. Use FFmpeg to create a generic 6-second video with fake Kannada audio
    # Let's just create a 6-second video with some noise as the "Kannada" audio
    os.system('ffmpeg -y -f lavfi -i testsrc=duration=6:size=1280x720:rate=30 -f lavfi -i aevalsrc="sin(440*2*PI*t)*0.5 + sin(880*2*PI*t)*0.5" -t 6 -c:v libx264 -c:a aac assets/kannada_sample.mp4')
    
    # 4. Use FFmpeg to encode the English audio property
    os.system('ffmpeg -y -i assets/tmp_eng.mp3 -acodec aac -ac 2 -ar 44100 assets/english_sample.aac')
    
    # Clean up temp mp3
    if os.path.exists("assets/tmp_eng.mp3"):
        os.remove("assets/tmp_eng.mp3")

if __name__ == "__main__":
    create_sample_files()
