"""
SREY Core Engine
----------------
Pipeline:
1. Local deterministic handlers (OS commands + Notes)
2. AI fallback (brain.py)

Both main.py and server.py should use this Assistant class.
"""

import threading

from brain import JarvisBrain
from core import CommandProcessor
from notes import NotesManager


NOTE_SAVE_TRIGGERS = (
    "remember that",
    "remember",
    "take a note",
    "take note",
)

NOTE_READ_TRIGGERS = (
    "read my notes",
    "what are my notes",
    "show my notes",
)

NOTE_CLEAR_TRIGGERS = (
    "clear my notes",
    "delete my notes",
)

NOTE_SEARCH_PREFIXES = (
    "search my notes for ",
    "find note ",
    "find notes ",
)


class Assistant:
    def __init__(self):
        self.brain = JarvisBrain()
        self.notes = NotesManager()
        self.commands = CommandProcessor()
        self._lock = threading.Lock()

    def _local_response(self, original_text: str) -> str:
        """Handle all deterministic commands before AI."""

        lower_text = original_text.lower().strip()

        try:
            # ----------------------------
            # 1. OS / Desktop Commands
            # ----------------------------
            os_result = self.commands.execute(original_text)
            if os_result:
                return os_result

            # ----------------------------
            # 2. Clear Notes
            # ----------------------------
            if any(trigger in lower_text for trigger in NOTE_CLEAR_TRIGGERS):
                return self.notes.clear_notes()

            # ----------------------------
            # 3. Search Notes
            # ----------------------------
            for prefix in NOTE_SEARCH_PREFIXES:
                if lower_text.startswith(prefix):
                    query = original_text[len(prefix):].strip()

                    if not query:
                        return "What should I search for?"

                    return self.notes.search_notes(query)

            # ----------------------------
            # 4. Read Notes
            # ----------------------------
            if any(trigger in lower_text for trigger in NOTE_READ_TRIGGERS):
                return self.notes.read_notes()

            # ----------------------------
            # 5. Save Note
            # ----------------------------
            for trigger in NOTE_SAVE_TRIGGERS:
                if lower_text.startswith(trigger):
                    content = original_text[len(trigger):].strip()

                    # Remove optional leading "to"
                    if content.lower().startswith("to "):
                        content = content[3:].strip()

                    # Remove optional ":" after trigger
                    if content.startswith(":"):
                        content = content[1:].strip()

                    if not content:
                        return "What would you like me to remember?"

                    return self.notes.save_note(content)

        except Exception as e:
            print(f"[LOCAL ERROR] {e}")
            return "I encountered an error while processing that locally."

        # Nothing matched → AI will handle it
        return ""

    def handle(self, user_text: str) -> str:
        """Main entry point used by every frontend."""

        user_text = (user_text or "").strip()

        if not user_text:
            return "I did not catch that."

        with self._lock:
            print(f"[Command] {user_text}")

            # Local commands first
            response_text = self._local_response(user_text)

            # AI fallback
            if not response_text:
                response_text = self.brain.process_prompt(user_text)

            return response_text