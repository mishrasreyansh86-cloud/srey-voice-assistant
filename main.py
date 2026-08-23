import os
import threading
import time

import eel
import keyboard
import psutil

from brain import JarvisBrain
from core import CommandProcessor
from notes import NotesManager
from voice import VoiceEngine

app_instance = None

NOTE_SAVE_TRIGGERS = ("remember", "take a note", "take note")
NOTE_READ_TRIGGERS = ("read my notes", "what are my notes", "show my notes")
NOTE_CLEAR_TRIGGERS = ("clear my notes", "delete my notes")
NOTE_SEARCH_PREFIXES = ("search my notes for ", "find note ", "find notes ")


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
        self.brain = JarvisBrain()
        self.notes = NotesManager()
        self.commands = CommandProcessor()
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

    def _local_response(self, command_text: str) -> str:
        os_result = self.commands.execute(command_text)
        if os_result:
            return os_result

        if any(trigger in command_text for trigger in NOTE_CLEAR_TRIGGERS):
            return self.notes.clear_notes()

        for prefix in NOTE_SEARCH_PREFIXES:
            if command_text.startswith(prefix):
                return self.notes.search_notes(command_text.replace(prefix, "", 1))

        if any(trigger in command_text for trigger in NOTE_READ_TRIGGERS):
            return self.notes.read_notes()

        if any(trigger in command_text for trigger in NOTE_SAVE_TRIGGERS):
            content = command_text
            for phrase in ("remember that", "remember", "take a note", "take note"):
                content = content.replace(phrase, "")
            return self.notes.save_note(content.strip())

        return ""

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
            command_text = user_text.lower()
            response_text = self._local_response(command_text)
            if not response_text:
                response_text = self.brain.process_prompt(user_text)

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