import pyttsx3

def live_text_to_speech_with_persona():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices') # Grab all system personas
    
    print("Select a Persona:")
    for index, v in enumerate(voices):
        print(f"[{index}] {v.name}")
        
    # Let the user choose the voice index dynamically
    try:
        chosen_index = int(input("Enter voice number (e.g., 0 or 1): "))
        if 0 <= chosen_index < len(voices):
            engine.setProperty('voice', voices[chosen_index].id)
            print(f"🎙️ Persona set to: {voices[chosen_index].name}\n")
        else:
            print("⚠️ Invalid index. Using system default.")
    except ValueError:
        print("⚠️ Invalid input. Using system default.")

    # Adjust speed rate
    engine.setProperty('rate', 160)

    print("👉 Type your text and press Enter. Type 'exit' to quit.\n")

    while True:
        user_text = input("🎤 Enter text to read: ")
        if user_text.strip().lower() == 'exit':
            print("👋 Goodbye!")
            break
        if not user_text.strip():
            continue
            
        engine.say(user_text)
        engine.runAndWait()

if __name__ == "__main__":
    live_text_to_speech_with_persona()