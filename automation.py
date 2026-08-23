import os
import re
import urllib.parse
import urllib.request
import webbrowser

import psutil
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.02

_VIDEO_ID_RE = re.compile(r'"videoId":"([a-zA-Z0-9_-]{11})"')
_WATCH_RE = re.compile(r"/watch\?v=([a-zA-Z0-9_-]{11})")
_YT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class DesktopAutomation:
    @staticmethod
    def _open_url(url: str) -> None:
        webbrowser.open(url, new=2)

    def _first_youtube_id(self, query: str) -> str:
        search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        request = urllib.request.Request(search_url, headers=_YT_HEADERS)
        with urllib.request.urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")

        for match in _VIDEO_ID_RE.finditer(html):
            video_id = match.group(1)
            if video_id != "00000000000":
                return video_id

        watch = _WATCH_RE.search(html)
        return watch.group(1) if watch else ""

    def play_on_youtube(self, query: str) -> str:
        def _open():
            try:
                video_id = self._first_youtube_id(query)
            except Exception as e:
                print(f"[YouTube] Could not resolve first video: {e}")
                video_id = ""
            if video_id:
                self._open_url(f"https://www.youtube.com/watch?v={video_id}&autoplay=1")
            else:
                encoded = urllib.parse.quote_plus(query)
                self._open_url(f"https://www.youtube.com/results?search_query={encoded}")

        import threading

        threading.Thread(target=_open, daemon=True).start()
        return f"Playing {query} on YouTube."

    def google_search(self, query: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        self._open_url(f"https://www.google.com/search?q={encoded}")
        return f"Searching Google for {query}."

    def set_volume(self, action: str = "up") -> str:
        action = action.lower()
        if "mute" in action or "unmute" in action:
            pyautogui.press("volumemute")
            return "Volume muted."
        key = "volumeup" if "up" in action or "increase" in action else "volumedown"
        pyautogui.press(key, presses=5, interval=0)
        return "Volume increased." if key == "volumeup" else "Volume decreased."

    def take_screenshot(self) -> str:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(desktop_path)
        return "Screenshot saved to your Desktop."

    def check_battery(self) -> str:
        battery = psutil.sensors_battery()
        if battery:
            charging = "plugged in" if battery.power_plugged else "on battery power"
            return f"Your battery is at {battery.percent}% and currently {charging}."
        return "Unable to detect battery status on this system."

    def open_app(self, app_name: str) -> str:
        pyautogui.press("win")
        pyautogui.write(app_name, interval=0)
        pyautogui.press("enter")
        return f"Opening {app_name}."

    def close_app(self, app_name: str) -> str:
        pyautogui.hotkey("alt", "f4")
        return f"Closing {app_name}."
