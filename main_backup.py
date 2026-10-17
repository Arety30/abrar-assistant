import os
import asyncio
import websockets
import ollama
import json
from dotenv import load_dotenv
from google import genai
from elevenlabs.client import AsyncElevenLabs

# 1. LOAD THE KEYS (Explicitly pointing to your new file)
env_path = os.path.expanduser("~/main.env")
load_dotenv(env_path)

# 2. SAFETY CHECK
if not os.getenv("GEMINI_API_KEY"):
    print(f"❌ CRITICAL ERROR: Could not find keys in {env_path}")
    print("Please check that the file exists and has the correct formatting.")
    exit(1)

# 3. INITIALIZE CLIENTS
eleven_client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- CONFIGURATION ---
# The 3CX Token (Leave as is for now, if it says 404/Unauthorized later, we will update this)
ACCESS_TOKEN = "REDACTED"

INSTANCES = {
    "PRIMARY": f"wss://1752.3cx.cloud/api/v1/callcontrol/ws?token={ACCESS_TOKEN}",
    "ALTERNATE": f"wss://1727.3cx.cloud/api/v1/callcontrol/ws?token={ACCESS_TOKEN}"
}

VOICE_MAP = {
    "1": "mPibZ3T7ryWsWgrKMFal", # Qatari Arabic
    "2": "rUaPbzcZIu8df8iNL9WZ", # Gulf Arabic
    "5": "l5LPd4RiIgGFgzEi8Smo", # American Eng
    "6": "Xb7hH8MSUJpSbSDYk0k2"  # British Eng
}

async def get_ai_response(text):
    route_prompt = f"Categorize: '{text}'. If it needs real-time facts/weather, respond 'SEARCH'. If coding, 'CODING'. Else 'GENERAL'."
    route_resp = await asyncio.to_thread(ollama.generate, model='deepseek-r1:7b', prompt=route_prompt)
    route = route_resp['response'].strip().upper()

    if "SEARCH" in route:
        print("🔍 Grounding via Gemini Cloud...")
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=text)
        return response.text
    elif "CODING" in route:
        print("💻 Running Local DeepSeek-Coder-V2...")
        resp = await asyncio.to_thread(ollama.generate, model='deepseek-coder-v2:lite', prompt=text)
        return resp['response']
    else:
        print("🧠 Running Local Gemma 2...")
        resp = await asyncio.to_thread(ollama.generate, model='gemma2:9b', prompt=text)
        return resp['response']

async def handle_call(line_id, uri):
    current_voice = VOICE_MAP["5"]
    print(f"🚀 {line_id}: Connecting...")
    try:
        async with websockets.connect(uri) as ws:
            print(f"✅ {line_id}: Bridge Established.")
            async for message in ws:
                data = json.loads(message)
                if data.get("event") == "dtmf":
                    digit = data.get("digit")
                    if digit in VOICE_MAP:
                        current_voice = VOICE_MAP[digit]
                        print(f"[{line_id}] Switched to Voice {digit}")
                        continue
                if data.get("event") == "media":
                    payload = data['media']['payload']
                    trans = await eleven_client.speech_to_text.convert(file=payload, model_id="scribe_v2")
                    if not trans.text.strip(): continue
                    ai_text = await get_ai_response(trans.text)
                    audio_gen = await eleven_client.text_to_speech.convert(
                        text=ai_text, voice_id=current_voice, model_id="eleven_flash_v2_5"
                    )
                    audio_out = b"".join([chunk async for chunk in audio_gen])
                    await ws.send(audio_out)
    except Exception as e:
        print(f"❌ {line_id} Connection Failed: {e}")

async def main():
    await asyncio.gather(
        handle_call("PRIMARY", INSTANCES["PRIMARY"]),
        handle_call("ALTERNATE", INSTANCES["ALTERNATE"])
    )

if __name__ == "__main__":
    asyncio.run(main())
