# 🤖 SREY — Voice Assistant

> A Python-based personal desktop voice assistant built to explore AI, voice interaction, and desktop automation.

---

## ✨ About

**SREY** is a personal voice assistant project I'm developing while learning Python and exploring AI.

The goal is to build an assistant that can understand voice commands, interact with AI models, perform desktop tasks, and provide useful everyday utilities.

This project is actively evolving as I learn and experiment with new ideas.

---

## 🚀 Current Features

* 🎙️ Voice interaction
* 🧠 AI-powered responses
* 💻 Desktop automation
* 🔎 Web search
* 📝 Notes and personal utilities
* 🧩 Modular Python architecture
* 🌐 Web-based assistant interface

---

## 🧠 AI Providers

SREY can work with multiple AI providers through environment-based configuration.

Currently supported:

* **Google Gemini**
* **Groq**

API keys are stored locally in `.env` and are **not included in this repository**.

---

## 🛠️ Built With

* **Python**
* **Eel**
* **Google Gemini API**
* **Groq API**
* **HTML**
* **CSS**
* **JavaScript**
* **Git & GitHub**

---

## 📂 Project Structure

```text
srey-voice-assistant/
│
├── main.py
├── brain.py
├── voice.py
├── automation.py
├── core.py
├── notes.py
├── requirements.txt
│
├── web/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── .gitignore
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/mishrasreyansh86-cloud/srey-voice-assistant.git
```

### 2. Open the project

```bash
cd srey-voice-assistant
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate it on Windows

```powershell
venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Create your `.env` file

Create a file named:

```text
.env
```

Add your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

Your `.env` file is ignored by Git and should **never be uploaded to GitHub**.

### 7. Run SREY

```bash
python main.py
```

---

## 🔐 Security

API keys and other secrets are kept outside the source code using environment variables.

The `.env` file is excluded through `.gitignore`.

**Never commit API keys, passwords, tokens, or other secrets to GitHub.**

---

## 🗺️ Roadmap

* [x] Basic voice assistant
* [x] AI integration
* [x] Desktop automation
* [x] Web interface
* [x] Multiple AI provider support
* [ ] Improve conversation memory
* [ ] Improve voice interaction
* [ ] Add more desktop controls
* [ ] Improve UI/UX
* [ ] Package the application for easier installation

---

## 📸 Screenshots

Screenshots will be added as the interface and features are refined.

---

## 👨‍💻 Author

**Sreyansh Mishra**

First-Year B.Tech CSE Student
GLA University, Mathura

Exploring **Python, AI, Data Science, and Cybersecurity**.

---

## ⭐ Project Status

🚧 **Active Development**

SREY is a learning-focused project that will continue to evolve as I develop my programming and software engineering skills.

---

> **Learn. Build. Break. Debug. Improve. Repeat.**
