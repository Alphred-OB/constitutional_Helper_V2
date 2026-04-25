import asyncio
import edge_tts

async def main():
    voices = await edge_tts.VoicesManager.create()
    all_voices = voices.voices
    for v in all_voices:
        if v["Name"].startswith("en-"):
            print(f"Name: {v['Name']}")

if __name__ == "__main__":
    asyncio.run(main())
