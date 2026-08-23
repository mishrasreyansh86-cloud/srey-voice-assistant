import os
import threading
import time
import webbrowser
from pathlib import Path

import psutil
import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from assistant import Assistant
from brain import _read_env_file

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
_read_env_file(ROOT / ".env")

app = FastAPI(title="Srey Neural Core")
assistant = Assistant()
psutil.cpu_percent(interval=None)


class CommandIn(BaseModel):
    text: str


class SpeakIn(BaseModel):
    text: str


@app.post("/api/command")
def api_command(body: CommandIn):
    return {"reply": assistant.handle(body.text)}


@app.post("/api/speak")
async def api_speak(body: SpeakIn):
    import edge_tts

    voice = os.environ.get("TTS_VOICE", "hi-IN-SwaraNeural").strip() or "hi-IN-SwaraNeural"
    rate = os.environ.get("TTS_RATE", "-22%").strip() or "-22%"
    pitch = os.environ.get("TTS_PITCH", "-6Hz").strip() or "-6Hz"
    text = (body.text or "").strip()
    if not text:
        return Response(status_code=400)

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    audio = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return Response(content=audio, media_type="audio/mpeg")


@app.get("/api/telemetry")
def api_telemetry():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
    }


app.mount("/", StaticFiles(directory=str(WEB), html=True), name="static")


def run():
    host = os.environ.get("WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB_PORT", "8000"))
    print("\n" + "=" * 50)
    print(" SREY // NEURAL CORE 2.0 - WEB")
    print("=" * 50)
    print(f"[WEB] Open http://127.0.0.1:{port}")
    if host == "127.0.0.1":
        print("[WEB] Phone access is disabled by default (security).")
        print("[WEB] To allow it on your Wi-Fi, set WEB_HOST=0.0.0.0 in .env")
        print("[WEB] WARNING: the API has no authentication. Only do this on a trusted network.")
    else:
        print("[WEB] Exposed to network (" + host + "). Phone: http://<this-pc-ip>:" + str(port))
        print("[WEB] WARNING: no authentication - anyone on this network can control SREY.")
    print("=" * 50 + "\n")

    def _open():
        time.sleep(1.1)
        webbrowser.open(f"http://127.0.0.1:{port}")

    threading.Thread(target=_open, daemon=True).start()
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run()
