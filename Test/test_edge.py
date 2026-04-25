import asyncio
import edge_tts

async def test():
    communicate = edge_tts.Communicate("Hello, this is a test.", "en-GB-SoniaNeural")
    chunks = []
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            chunks.append(chunk['data'])
    audio = b''.join(chunks)
    with open("test_tts.mp3", "wb") as f:
        f.write(audio)
    print(f"Success — wrote {len(audio)} bytes to test_tts.mp3")

asyncio.run(test())