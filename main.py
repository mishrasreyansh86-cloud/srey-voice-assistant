import os
import threading
import time

import eel
import keyboard
import psutil

from assistant import Assistant
from voice import VoiceEngine

app_instance = None


def run_boot_sequence():
    print("\n" + "=" * 50)
    print(" SREY // NEURAL CORE 2.0 - MONOCHROME BOOT")
    print("=" * 50)
    for step in (
        "SREY INDUSTRIES // BOOT SEQUENCE",
        "INITIALIZING NEURAL CORE...",
        "VOICE ENGINE ONLINE...",
        "SYSTEM TELEMETRY READY...",
        "LANGUAGE CORE ONLINE...",
        "WELCOME SREYANSH.",
    ):
        print(f"[BOOT] ❯ {step}")
    print("=" * 50 + "\n")


def _safe_ui(fn, *args):
    try:
        fn(*args)()
    except Exception:
        pass


class JarvisApp:
    def __init__(self):
        global app_instance
        app_instance = self

        self.voice = VoiceEngine()
        self.engine = Assistant()
        self._busy = threading.Lock()
        self._pending_command = None
        
        web_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        eel.init(web_folder)
        
        try:
            keyboard.add_hotkey("ctrl+space", self.trigger_from_hotkey)
        except Exception as e:
            print(f"[Hotkey] Could not bind Ctrl+Space: {e}")

        self.telemetry_active = True
        threading.Thread(target=self.broadcast_telemetry, daemon=True).start()

    def broadcast_telemetry(self):
        psutil.cpu_percent(interval=None)
        while self.telemetry_active:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                eel.update_telemetry(cpu, ram)()
            except Exception:
                pass
            time.sleep(3)

    def trigger_from_hotkey(self):
        self.voice.interrupt()
        _safe_ui(eel.set_ai_state, "LISTENING...")

    def process_ai_response(self, user_text: str):
        user_text = (user_text or "").strip()
        if not user_text:
            _safe_ui(eel.set_ai_state, "IDLE")
            return

        if not self._busy.acquire(blocking=False):
            self._pending_command = user_text
            return

        try:
            print(f"[Command] {user_text}")
            _safe_ui(eel.set_ai_state, "THINKING...")
            response_text = self.engine.handle(user_text)

            _safe_ui(eel.set_ai_state, "SPEAKING...")
            _safe_ui(eel.display_ai_response, response_text)
            self.voice.speak(
                text=response_text,
                callback=lambda: _safe_ui(eel.set_ai_state, "LISTENING..."),
            )
        except Exception as e:
            print(f"[Process Error]: {e}")
            _safe_ui(eel.set_ai_state, "IDLE")
        finally:
            self._busy.release()
            queued = self._pending_command
            self._pending_command = None
            if queued:
                threading.Thread(
                    target=self.process_ai_response,
                    args=(queued,),
                    daemon=True,
                ).start()

    def run(self):
        run_boot_sequence()
        eel.start("index.html", size=(1000, 700), port=8000, mode="chrome")


@eel.expose
def handle_user_speech(user_text):
    if app_instance:
        app_instance.voice.interrupt()
        threading.Thread(
            target=app_instance.process_ai_response,
            args=(user_text,),
            daemon=True,
        ).start()


if __name__ == "__main__":
    JarvisApp().run()