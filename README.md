# JARVIS AI Desktop Assistant 🎙️

A futuristic, modern, and multithreaded AI desktop assistant built with Python, CustomTkinter, and Google Gemini. 

JARVIS is designed to be a local voice assistant that helps you manage your PC, take notes, check the weather, and answer questions conversationally without freezing or locking up your system.

## 🌟 Features
* **Modern Glassmorphism UI:** Built using CustomTkinter with a dark aesthetic.
* **Conversational AI:** Powered by Google's `gemini-1.5-flash` for high-speed, contextual responses.
* **Multithreaded Voice Engine:** Uses `speech_recognition` and `pyttsx3` running in the background so the GUI never freezes.
* **Smart Notes:** Tell JARVIS to "remember" something, and it will save it with a timestamp.
* **Desktop Automation:** Open everyday apps like Chrome, VS Code, and Notepad using your voice.
* **Live System Telemetry:** Real-time updates on your CPU, RAM, and Battery usage.
* **Weather Integration:** Get the current temperature and wind speed for any city instantly.

## 🛠️ Prerequisites
* Python 3.13 or higher installed and added to your system PATH.
* An active microphone connected to your PC.
* A free [Google Gemini API Key](https://aistudio.google.com/).

## 🚀 Installation

1. **Clone or Download the Repository:**
   Open your terminal and navigate to the project folder.

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate