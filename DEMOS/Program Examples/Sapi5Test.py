import pyttsx3
import time

def test_all_sapi5_voices(text="This is a test of the emergency broadcast system. This is a test of the emergency broadcast system."):
    # Initialize the engine
    engine = pyttsx3.init()

    # Get list of available voices
    voices = engine.getProperty('voices')

    print(f"\nTesting {len(voices)} available SAPI5 voices:")
    print("=" * 50)

    for i, voice in enumerate(voices):
        # Set the current voice
        engine.setProperty('voice', voice.id)

        # Get voice properties
        voice_name = voice.name
        voice_lang = voice.languages[0] if voice.languages else 'Unknown'

        print(f"\nVoice {i+1}: {voice_name} ({voice_lang})")
        print(f"ID: {voice.id}")
        print(f"Gender: {'Male' if voice.gender == 'male' else 'Female'}")
        print(f"Age: {'Young' if voice.age == 'young' else 'Adult' if voice.age == 'adult' else 'Senior'}")

        # Test the voice
        print(f"\nTesting voice {i+1}...")
        engine.say(text)
        engine.runAndWait()

        # Add a small delay between tests
        time.sleep(0.5)

    print("\nCompleted all voice tests!")
    print("=" * 50)

if __name__ == "__main__":
    # Test text
    test_text = """
    This is a comprehensive SAPI5 voice test. The system will now demonstrate all available voices.
    Please listen carefully to ensure all voices are functioning properly.
    The following is a sample sentence: "The quick brown fox jumps over the lazy dog."
    """

    test_all_sapi5_voices(test_text)