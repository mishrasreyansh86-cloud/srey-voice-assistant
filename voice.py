import asyncio
import os
import queue
import re
import tempfile
import threading
import time
from pathlib import Path

from brain import _read_env_file

_MARKDOWN_RE = re.compile(r"[*#_`|~>-]+")
_SPACE_RE = re.compile(r"\s+")


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip() or default


class VoiceEngine:
    def __init__(self):
        _read_env_file(Path(__file__).resolve().parent / ".env")

        # North Indian / UP-style neural voice (Hindi). Swap to en-IN-PrabhatNeural for English-only.
        self.voice = _env("TTS_VOICE", "hi-IN-MadhurNeural")
        self.rate = _env("TTS_RATE", "-22%")
        self.pitch = _env("TTS_PITCH", "-6Hz")
        self.speech_queue = queue.Queue()
        self._use_neural = True
        self._skip_callback = False
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    @staticmethod
    def clean_for_speech(text: str) -> str:
        if not text:
            return ""
        cleaned = _MARKDOWN_RE.sub(" ", text)
        return _SPACE_RE.sub(" ", cleaned).strip()

    def _speak_neural(self, text: str) -> None:
        import edge_tts
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = tmp.name
        tmp.close()

        async def _synth():
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
            )
            await communicate.save(tmp_path)

        asyncio.run(_synth())
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and not self._skip_callback:
            time.sleep(0.05)
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    def _speak_sapi(self, engine, text: str) -> None:
        engine.setProperty("rate", 135)
        engine.say(text)
        engine.runAndWait()

    def _speech_worker(self):
        fallback_engine = None
        try:
            import edge_tts  # noqa: F401
            import pygame

            pygame.mixer.init(frequency=24000)
            print(f"[Voice] Neural TTS ready: {self.voice} at {self.rate}")
        except Exception as e:
            print(f"[Voice] Neural TTS unavailable ({e}). Falling back to Windows SAPI.")
            self._use_neural = False
            try:
                import pyttsx3

                fallback_engine = pyttsx3.init()
                fallback_engine.setProperty("rate", 135)
            except Exception as init_error:
                print(f"[Voice Init Error]: {init_error}")

        while True:
            text, callback = self.speech_queue.get()
            try:
                spoken_text = self.clean_for_speech(text)
                if spoken_text:
                    self._skip_callback = False
                    if self._use_neural:
                        self._speak_neural(spoken_text)
                    elif fallback_engine:
                        self._speak_sapi(fallback_engine, spoken_text)
            except Exception as e:
                print(f"[TTS Execution Error]: {e}")
            finally:
                skipped = self._skip_callback
                self._skip_callback = False
                if callback and not skipped:
                    try:
                        callback()
                    except Exception as e:
                        print(f"[Callback Error]: {e}")
                self.speech_queue.task_done()

    def interrupt(self):
        self._skip_callback = True
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def speak(self, text: str, callback=None):
        if not text:
            if callback:
                callback()
            return

        while True:
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break

        self.speech_queue.put((text, callback))
