import json
import os
import urllib.error
import urllib.request
from pathlib import Path

SYSTEM_INSTRUCTION = (
    "You are Srey, a calm desktop voice assistant from North India. "
    "Speak in simple, natural Indian English with a relaxed Uttar Pradesh tone. "
    "Reply in one or two short spoken sentences of plain text. "
    "No markdown, lists, bullets, asterisks, hashes, or tables."
)

MAX_CHAT_TURNS = 12
MAX_OUTPUT_TOKENS = 180
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _read_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ[key] = value


class JarvisBrain:
    def __init__(self):
        _read_env_file(Path(__file__).resolve().parent / ".env")
        self.groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash").strip()
        self.provider = os.environ.get("AI_PROVIDER", "auto").strip().lower()
        self.messages = []
        self._turns = 0
        self.gemini_client = None
        self.gemini_chat = None

        if self.provider == "auto":
            self.provider = "groq" if self.groq_key else "gemini"

        if self.provider == "groq":
            if not self.groq_key:
                print("[Brain] Missing GROQ_API_KEY. Get a free key at https://console.groq.com/keys")
                return
            print(f"[Brain] Using Groq ({self.groq_model}).")
            return

        if not self.gemini_key:
            print("[Brain] Missing GEMINI_API_KEY.")
            return
        try:
            from google import genai
            from google.genai import types

            self._gemini_types = types
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            self._reset_gemini_chat()
            print(f"[Brain] Using Gemini ({self.gemini_model}).")
        except Exception as e:
            print(f"[Brain Init Error]: {e}")

    def _reset_gemini_chat(self):
        if not self.gemini_client:
            return
        self.gemini_chat = self.gemini_client.chats.create(
            model=self.gemini_model,
            config=self._gemini_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.6,
            ),
        )
        self._turns = 0

    def process_prompt(self, prompt: str) -> str:
        if self.provider == "groq":
            return self._ask_groq(prompt)
        return self._ask_gemini(prompt)

    def _ask_groq(self, prompt: str) -> str:
        if not self.groq_key:
            return "Groq is not connected. Add GROQ_API_KEY to your .env file."

        if self._turns >= MAX_CHAT_TURNS:
            self.messages = []
            self._turns = 0

        self.messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.groq_model,
            "temperature": 0.6,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}, *self.messages],
        }
        request = urllib.request.Request(
            GROQ_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if not text:
                return "I did not catch a response. Please try again."
            self.messages.append({"role": "assistant", "content": text})
            self._turns += 1
            return text
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"[Groq HTTP {e.code}]: {body}")
            if e.code == 401:
                return "The Groq API key is invalid. Create a new key at console.groq.com."
            if e.code == 429:
                return "Groq is rate-limited for a moment. Please try again shortly."
            if e.code == 404:
                return "That Groq model is unavailable. Try GROQ_MODEL=llama-3.1-8b-instant in .env."
            self.messages.pop()
            return "I encountered an error talking to Groq."
        except Exception as e:
            print(f"[Groq Error]: {e}")
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()
            return "I encountered an error connecting to my neural core."

    def _ask_gemini(self, prompt: str) -> str:
        if not self.gemini_client or not self.gemini_chat:
            return "Gemini is not connected. Switch to Groq or check GEMINI_API_KEY."

        try:
            if self._turns >= MAX_CHAT_TURNS:
                self._reset_gemini_chat()
            response = self.gemini_chat.send_message(prompt)
            self._turns += 1
            if response and response.text:
                return response.text.strip()
            return "I did not catch a response. Please try again."
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("[Gemini Quota Exceeded]: Free tier limit reached.")
                return "Gemini quota is exhausted. Add a free Groq key to .env as GROQ_API_KEY."
            print(f"[Gemini Error]: {e}")
            return "I encountered an error connecting to Gemini."
