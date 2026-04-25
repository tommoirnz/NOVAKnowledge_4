import pythoncom
import win32com.client
import time


def test_all_sapi5_voices_safe():
    """Test all available SAPI5 voices safely, handling corrupted entries."""

    print("=" * 60)
    print("SAPI5 Voice System Test (Safe Version)")
    print("Each voice will announce its own name")
    print("=" * 60)

    # Initialize COM
    pythoncom.CoInitialize()

    try:
        # Create SAPI speaker
        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        # Get all voices
        voices = speaker.GetVoices()
        voice_count = voices.Count

        print(f"\n📢 Found {voice_count} SAPI5 voice(s) on your system")
        print("-" * 60)

        # Store voice info
        voice_list = []

        # First, enumerate all voices and collect info safely
        for i in range(voice_count):
            voice = voices.Item(i)

            # Get voice name safely
            try:
                name = voice.GetDescription()
            except:
                name = f"Unknown Voice {i}"

            # Get voice details safely (with error handling)
            lang = "Unknown"
            gender = "Unknown"
            age = "Unknown"

            # Try to get attributes individually with error handling
            try:
                lang_attr = voice.GetAttribute("Language")
                if lang_attr:
                    lang = lang_attr
            except:
                pass

            try:
                gender_attr = voice.GetAttribute("Gender")
                if gender_attr:
                    gender = gender_attr
            except:
                pass

            try:
                age_attr = voice.GetAttribute("Age")
                if age_attr:
                    age = age_attr
            except:
                pass

            # Get voice ID safely
            try:
                voice_id = voice.Id
            except:
                voice_id = "Unknown"

            voice_info = {
                'index': i,
                'name': name,
                'id': voice_id,
                'language': lang,
                'gender': gender,
                'age': age,
                'voice_obj': voice  # Store the voice object for later use
            }
            voice_list.append(voice_info)

            # Print voice info
            print(f"\n🎤 Voice #{i}:")
            print(f"   Name: {name}")
            print(f"   Language code: {lang}")
            print(f"   Gender: {gender}")
            print(f"   Age: {age}")
            print(f"   ID: {str(voice_id)[:60]}...")

        print("\n" + "=" * 60)
        print("🔊 TEST SEQUENCE: Each voice will now speak")
        print("=" * 60)

        # Test each voice safely
        working_voices = []

        for voice_info in voice_list:
            print(f"\n▶ Testing Voice #{voice_info['index']}: {voice_info['name']}")

            try:
                # Select this voice
                speaker.Voice = voice_info['voice_obj']

                # Set normal speaking rate
                speaker.Rate = 0
                speaker.Volume = 100

                # Have the voice introduce itself
                intro_text = f"Hello. I am voice number {voice_info['index']}. My name is {voice_info['name']}. This is a test of the SAPI five text to speech system."

                print(f"   Speaking: {intro_text[:50]}...")

                # Speak (async to allow interruption detection)
                speaker.Speak(intro_text, 1)  # 1 = async

                # Wait for completion with visual feedback
                timeout = 0
                while speaker.Status.RunningState == 2 and timeout < 300:  # 30 second timeout
                    time.sleep(0.1)
                    timeout += 1

                working_voices.append(voice_info)
                print(f"   ✅ Voice #{voice_info['index']} spoke successfully")

                # Small pause between voices
                time.sleep(0.5)

            except Exception as e:
                print(f"   ❌ Failed to speak with voice #{voice_info['index']}: {e}")

        print("\n" + "=" * 60)
        print(f"✅ Testing complete! {len(working_voices)} out of {voice_count} voices worked")
        print("=" * 60)

        return voice_list, working_voices

    except Exception as e:
        print(f"\n❌ Error during voice test: {e}")
        import traceback
        traceback.print_exc()
        return None, None

    finally:
        # Cleanup COM
        pythoncom.CoUninitialize()


def fix_corrupted_voices_automatically():
    """Automatically fix corrupted voice registry entries."""

    import winreg
    import ctypes

    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    if not is_admin():
        print("⚠️ Registry fixes require Administrator privileges")
        print("Please run this script as Administrator to fix corrupted entries")
        return False

    print("\n🔧 Attempting to fix corrupted voice registry entries...")

    # Path to SAPI5 Voices in registry
    voice_key = r"SOFTWARE\Microsoft\Speech\Voices\Tokens"

    try:
        # Open the Tokens key
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, voice_key, 0, winreg.KEY_READ) as tokens_key:
            i = 0
            fixed_count = 0

            while True:
                try:
                    # Enumerate each voice token subkey
                    token_name = winreg.EnumKey(tokens_key, i)
                    token_path = f"{voice_key}\\{token_name}"

                    # Open the specific voice token
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, token_path, 0,
                                        winreg.KEY_ALL_ACCESS) as token_subkey:
                        try:
                            # Read the Attributes value
                            attributes, reg_type = winreg.QueryValueEx(token_subkey, "Attributes")

                            # Check if it contains a semicolon (corrupted)
                            if ';' in attributes:
                                print(f"Found corrupted voice: {token_name}")
                                print(f"  Original attributes: {attributes}")

                                # Fix by taking first part before semicolon
                                fixed_attributes = attributes.split(';')[0]

                                # Write back the fixed value
                                winreg.SetValueEx(token_subkey, "Attributes", 0, reg_type, fixed_attributes)
                                print(f"  Fixed attributes: {fixed_attributes}")
                                fixed_count += 1

                        except FileNotFoundError:
                            # No Attributes value, skip
                            pass

                    i += 1

                except WindowsError:
                    # No more subkeys
                    break

            print(f"\n✅ Fixed {fixed_count} corrupted voice entries")
            return fixed_count > 0

    except Exception as e:
        print(f"Error accessing registry: {e}")
        return False


def test_working_voices_only():
    """Test only the voices that are known to work (Microsoft voices)."""

    print("=" * 60)
    print("Testing Microsoft Voices Only")
    print("=" * 60)

    pythoncom.CoInitialize()

    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        voices = speaker.GetVoices()

        working_count = 0

        for i in range(voices.Count):
            try:
                voice = voices.Item(i)
                name = voice.GetDescription()

                # Skip CereVoice voices (they're corrupted)
                if "CereVoice" in name:
                    print(f"⏭️ Skipping {name} (corrupted)")
                    continue

                print(f"\n▶ Testing {name}")
                speaker.Voice = voice
                speaker.Rate = 0

                # Brief test phrase
                speaker.Speak(f"Hello from {name}", 1)

                timeout = 0
                while speaker.Status.RunningState == 2 and timeout < 100:
                    time.sleep(0.1)
                    timeout += 1

                print(f"   ✅ Working")
                working_count += 1

            except Exception as e:
                print(f"   ❌ Failed: {e}")

        print(f"\n✅ Found {working_count} working Microsoft voices")

    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    print("\n🎤 SAPI5 Voice System Test")
    print("=" * 60)

    # Option 1: Safe test that handles corrupted voices
    print("\n1. Running safe voice test...")
    all_voices, working_voices = test_all_sapi5_voices_safe()

    if working_voices:
        print("\n" + "=" * 60)
        print("📋 WORKING VOICES SUMMARY")
        print("=" * 60)
        for v in working_voices:
            print(f"Voice {v['index']}: {v['name']}")

    # Option 2: Offer to fix registry
    print("\n" + "=" * 60)
    print("🔧 Registry Fix Option")
    print("The CereVoice voices (1-6) have corrupted registry entries")
    fix = input("Would you like to attempt to fix them? (y/n): ").lower().strip()

    if fix == 'y':
        fix_corrupted_voices_automatically()
        print("\nAfter fixing, run the test again to verify.")

    # Option 3: Test only Microsoft voices
    print("\n" + "=" * 60)
    print("📢 Testing only Microsoft voices...")
    test_working_voices_only()

    input("\nPress Enter to exit...")