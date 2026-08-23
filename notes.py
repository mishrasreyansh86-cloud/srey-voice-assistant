from datetime import datetime
from pathlib import Path


class NotesManager:
    def __init__(self):
        self.directory = Path(__file__).resolve().parent / "data"
        self.filepath = self.directory / "notes.txt"
        self.directory.mkdir(parents=True, exist_ok=True)
        self._cache = None

    def _load_cache(self) -> str:
        if self._cache is not None:
            return self._cache
        if not self.filepath.is_file():
            self._cache = ""
            return self._cache
        self._cache = self.filepath.read_text(encoding="utf-8")
        return self._cache

    def save_note(self, content: str) -> str:
        content = content.strip()
        if not content:
            return "I cannot save an empty note."

        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            line = f"[{timestamp}] {content}\n"
            with open(self.filepath, "a", encoding="utf-8") as file:
                file.write(line)
            if self._cache is None:
                self._load_cache()
            else:
                self._cache += line
            return "I have saved that note for you."
        except Exception as e:
            self._cache = None
            return f"Failed to save your note. Error: {e}"

    def read_notes(self) -> str:
        try:
            notes = self._load_cache().strip()
            if not notes:
                return "You do not have any saved notes yet."
            return f"Here are your notes:\n\n{notes}"
        except Exception as e:
            self._cache = None
            return f"Could not read notes. Error: {e}"

    def search_notes(self, keyword: str) -> str:
        keyword = keyword.lower().strip()
        if not keyword:
            return "Please tell me what to search for in your notes."

        try:
            notes = self._load_cache()
            if not notes.strip():
                return "You don't have any saved notes to search through."
            matching_lines = [line.strip() for line in notes.splitlines() if keyword in line.lower()]
            if not matching_lines:
                return f"I found no notes containing the keyword '{keyword}'."
            return f"Found {len(matching_lines)} matching note(s):\n" + "\n".join(matching_lines)
        except Exception as e:
            self._cache = None
            return f"Error while searching notes: {e}"

    def clear_notes(self) -> str:
        try:
            self.filepath.write_text("", encoding="utf-8")
            self._cache = ""
            return "All your saved notes have been cleared."
        except Exception as e:
            self._cache = None
            return f"Failed to clear notes: {e}"
