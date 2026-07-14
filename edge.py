import asyncio
import os
import time
from gtts import gTTS
import edge_tts
import pygame

# The 3-sentence script to test articulation, pacing, and natural flow
TEST_TEXT = (
    "Welcome to the ultimate text-to-speech engine showdown. "
    "We are comparing standard Google TTS against Microsoft Edge Neural voices. "
    "Listen carefully to the differences in breathing, inflection, and tone quality. The PPG sensor is the most common hardware used in smartwatches for blood pressure monitoring. It consists of light-emitting diodes (LEDs) us usally green or infrared and a photo diode.   Pulse Wave Analysis (PWA):The LEDs shine light through the skin into the underlying blood vessels. As the heart beats, the volume of blood in the arteries changes, causing variations in light absorption. The photo detector measures these changes to generate a pulse waveform. Algorithms analyze the shape and features of this wave to estimate blood pressure."


)

GTTS_FILE = "output_gtts.mp3"
EDGE_FILE = "output_edge.mp3"

def play_audio_file(file_path):
    """Helper function to cleanly play an MP3 using pygame"""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    
    # Wait until the audio finishes playing
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
        
    pygame.mixer.quit()

async def generate_audio():
    # ---- 1. Generate using gTTS ----
    print("\n🤖 Generating with gTTS (Google Cloud)...")
    tts_gtts = gTTS(text=TEST_TEXT, lang='en', tld='com')
    tts_gtts.save(GTTS_FILE)
    print(f"✅ Saved standard voice to: {GTTS_FILE}")

    # ---- 2. Generate using edge-tts ----
    print("\n✨ Generating with edge-tts (Microsoft Neural)...")
    communicate = edge_tts.Communicate(TEST_TEXT, "en-US-EmmaNeural")
    await communicate.save(EDGE_FILE)
    print(f"✅ Saved premium neural voice to: {EDGE_FILE}")

def main():
    # Run the asynchronous audio generation
    asyncio.run(generate_audio())
    
    print("\n" + "="*50)
    print("🎧 STARTING THE AUDIO SHOWDOWN 🎧")
    print("="*50)
    
    # ---- 3. Play gTTS ----
    print("\n▶️ Playing Candidate #1: Standard gTTS...")
    play_audio_file(GTTS_FILE)
    
    print("\n⏳ Pausing for 2 seconds...")
    time.sleep(2)
    
    # ---- 4. Play Edge TTS ----
    print("\n▶️ Playing Candidate #2: Premium Edge Neural (Emma)...")
    play_audio_file(EDGE_FILE)
    
    print("\n🏁 Showdown complete! Which one sounded more human to you?")

if __name__ == "__main__":
    main()