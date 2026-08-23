import threading

from brain import JarvisBrain
from core import CommandProcessor
from notes import NotesManager

NOTE_SAVE_TRIGGERS = ("remember", "take a note", "take note")
NOTE_READ_TRIGGERS = ("read my notes", "what are my notes", "show my notes")
NOTE_CLEAR_TRIGGERS = ("clear my notes", "delete my notes")
NOTE_SEARCH_PREFIXES = ("search my notes for ", "find note ", "find notes ")


class Assistant:
    def __init__(self):
        self.brain = JarvisBrain()
        self.notes = NotesManager()
        self.commands = CommandProcessor()
        self._lock = threading.Lock()

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

    def handle(self, user_text: str) -> str:
        user_text = (user_text or "").strip()
        if not user_text:
            return "I did not catch that."

        with self._lock:
            print(f"[Command] {user_text}")
            response_text = self._local_response(user_text.lower())
            if not response_text:
                response_text = self.brain.process_prompt(user_text)
            return response_text
