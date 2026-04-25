import pyttsx3

def initialize_tts():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    # Print available voices with proper formatting
    print("Available Voices:")
    print("--------------------------------------------------")
    print(f"{'ID':<5} | {'Name':<25} | {'Languages':<15} | {'Gender':<8} | {'Age':<5}")
    print("--------------------------------------------------")

    for voice in voices:
        try:
            languages = voice.languages if hasattr(voice, 'languages') else "N/A"
            age = voice.age if hasattr(voice, 'age') else "N/A"
            print(f"{voice.id[:4]:<5} | {voice.name[:25]:<25} | {languages:<15} | {voice.gender[:7]:<8} | {age:<5}")
        except AttributeError as e:
            print(f"Error processing voice {voice.id}: {str(e)}")

    return engine

def main():
    engine = initialize_tts()
    if engine:
        print("TTS System Initialization Complete")
        print("Listed available voices above")
    else:
        print("Error initializing TTS engine")

if __name__ == "__main__":
    main()