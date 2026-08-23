import os
import re
import subprocess
import platform
import datetime
import psutil
from automation import DesktopAutomation

_INFO_WORDS = ("how to", "who", "what", "why", "rules", "game", "chess")
_MEDIA_TRIGGERS = ("song", "music", "youtube", "yt", "track", "audio")
_FILLERS = re.compile(
    r"\b(please|can you|could you|would you|will you|i want you to|i want to|just|for me|now)\b"
)
_GOOGLE_PATTERNS = [
    re.compile(r"(?:search google for|google search for|google search|google for|google)\s+(.+)"),
    re.compile(r"search(?:\s+for)?\s+(.+?)\s+on google"),
    re.compile(r"look up\s+(.+)"),
    re.compile(r"find\s+(.+)\s+on google"),
    re.compile(r"^search for\s+(.+)"),
]


class CommandProcessor:
    def __init__(self):
        self.automation = DesktopAutomation()
        self._is_windows = platform.system() == "Windows"

    def execute(self, command: str) -> str | None:
        cmd = _FILLERS.sub(" ", command.lower())
        cmd = " ".join(cmd.split()).strip()
        if not cmd:
            return None

        if cmd in {"stop", "shut up", "be quiet", "quiet", "chup", "enough"}:
            return "Okay."

        if self._is_play_command(cmd) and not any(word in cmd for word in _INFO_WORDS):
            song_query = self._extract_play_query(cmd)
            try:
                return self.automation.play_on_youtube(song_query)
            except Exception:
                return f"Could not stream {song_query}."

        google_query = self._extract_google_query(cmd)
        if google_query:
            return self.automation.google_search(google_query)

        if "weather" in cmd:
            return self.automation.google_search(cmd)

        if cmd.startswith("open ") or cmd.startswith("launch "):
            return self._open_named_app(cmd.replace("launch", "open", 1).replace("open", "", 1).strip())

        if cmd.startswith("close ") or cmd in {"close", "close it", "close window"}:
            return self.automation.close_app(cmd.replace("close", "", 1).strip() or "window")

        if "screenshot" in cmd or "screen shot" in cmd:
            return self.automation.take_screenshot()

        if "volume" in cmd or "mute" in cmd or "unmute" in cmd:
            if "mute" in cmd or "unmute" in cmd:
                return self.automation.set_volume("mute")
            if "down" in cmd or "lower" in cmd or "decrease" in cmd:
                return self.automation.set_volume("down")
            return self.automation.set_volume("up")

        if "battery" in cmd:
            return self.automation.check_battery()

        if "disk space" in cmd or "storage" in cmd:
            usage = psutil.disk_usage("C:" if self._is_windows else "/")
            free_gb = round(usage.free / (1024 ** 3), 1)
            drive = "Drive C" if self._is_windows else "This drive"
            return f"{drive} has {free_gb} gigabytes of free space remaining."

        if re.search(r"\btime\b", cmd) and "concept of time" not in cmd:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current system time is {current_time}."

        if re.search(r"\bdate\b", cmd) and not any(word in cmd for word in ("update", "candidate")):
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {current_date}."

        return None

    def _extract_google_query(self, cmd: str) -> str:
        if "my notes" in cmd or "note" in cmd:
            return ""
        for pattern in _GOOGLE_PATTERNS:
            match = pattern.search(cmd)
            if match:
                return match.group(1).strip()
        return ""

    def _is_play_command(self, cmd: str) -> bool:
        if cmd.startswith("play ") or cmd.startswith("put on "):
            return True
        return "play" in cmd and any(trigger in cmd for trigger in _MEDIA_TRIGGERS)

    def _extract_play_query(self, cmd: str) -> str:
        query = cmd
        for phrase in (
            "on youtube",
            "on yt",
            "from youtube",
            "youtube",
            "put on",
            "play me",
            "play a",
            "play the",
            "play",
            "song",
            "music",
            "track",
            "video",
        ):
            query = query.replace(phrase, " ")
        query = " ".join(query.split()).strip()
        return query or "music mix"

    def _open_named_app(self, app_name: str) -> str:
        if "chrome" in app_name:
            return self._launch("chrome", ["google-chrome"], "Launching Google Chrome.", "Could not locate Google Chrome.")
        if "vscode" in app_name or app_name == "code" or "vs code" in app_name:
            return self._launch("code", ["code"], "Initializing Visual Studio Code.", "Could not launch VS Code.")
        if "notepad" in app_name:
            return self._launch("notepad", ["gedit"], "Opening Notepad.", "Could not open Notepad.")
        return self.automation.open_app(app_name)

    def _launch(self, windows_target: str, unix_cmd: list, ok: str, fail: str) -> str:
        try:
            if self._is_windows:
                os.startfile(windows_target)
            else:
                subprocess.Popen(unix_cmd)
            return ok
        except Exception:
            return fail
