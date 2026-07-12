import os
import time
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import pygame

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Grab the API key
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("❌ Error: ELEVENLABS_API_KEY not found in .env file!")
    exit(1)

# 3. Initialize the ElevenLabs client
client = ElevenLabs(api_key=api_key)

def text_to_speech_and_play(text_to_speak, filename="output.mp3"):
    try:
        print("⏳ Sending text to ElevenLabs...")
        
        # 4. Generate the audio using the new .convert() structure
        audio_response = client.text_to_speech.convert(
            text=text_to_speak,
            voice_id="Xb7hH8MSUJpSbSDYk0k2",  # Pre-made voice ID (Adam)
            model_id="eleven_multilingual_v2"
        )
        
        # 5. Save the chunks to an audio file
        with open(filename, "wb") as f:
            for chunk in audio_response:
                if chunk:
                    f.write(chunk)
        print(f"✅ Audio saved successfully as '{filename}'")

        # 6. Initialize pygame mixer and play the audio
        print("🔊 Playing audio...")
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        # Keep the script running while the audio plays
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        # Clean up audio player resources
        pygame.mixer.quit()
        print("🏁 Done playing!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    # Test text
    sample_text = "Welcome back, Justice. Your Eleven Labs setup is officially running through Python!"
    text_to_speech_and_play(sample_text)