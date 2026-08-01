# 🧠 Mental Health AI Chatbot
https://mental-health-chatbot-qk8w.onrender.com/

An AI-powered mental health support chatbot built using **Django** and **OpenRouter (LLMs)**.
This application provides a safe, supportive, and interactive environment where users can express their thoughts and receive empathetic, human-like responses.

---

## 🌟 Project Overview

This project simulates a real-world conversational AI system similar to ChatGPT but focused specifically on **mental wellness support**.

Users can:

* Create multiple conversations
* Interact with an AI assistant
* Manage and organize chats
* Share conversations with others

The system uses **Large Language Models (LLMs)** to generate responses that are supportive, structured, and natural.

---

## 🚀 Features

### 🧑‍💻 User Features

* 🔐 User Authentication (Login / Signup / Logout)
* 💬 Chat with AI assistant
* 📂 Multiple chat sessions (like ChatGPT)
* ✏️ Rename chats
* 🗑️ Delete chats
* 🔗 Share chat via link
* 🎯 Clean and minimal UI (ChatGPT-inspired)
* ⌨️ Send message using Enter key

---

### 🤖 AI Features

* Empathetic mental health responses
* Human-like conversational tone
* Structured replies (not robotic)
* Safe fallback handling if API fails
* Clean response formatting (no markdown clutter)

---

## 🛠️ Tech Stack

| Layer      | Technology            |
| ---------- | --------------------- |
| Backend    | Django (Python)       |
| Frontend   | HTML, CSS, JavaScript |
| Database   | SQLite (default)      |
| AI API     | OpenRouter (LLMs)     |
| Deployment | Render                |

---

## 📁 Project Structure

```
mental-health-chatbot/
│
├── mentalhealth_project/        # Main Django project
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── chatbot/                    # Core application
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│
├── templates/                  # Frontend templates
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│
├── manage.py
├── requirements.txt
├── .gitignore
├── README.md
```

---

## ⚙️ Installation Guide

### 1️⃣ Clone Repository

```
git clone https://github.com/bhargav20-ui/mental-health-chatbot.git
cd mental-health-chatbot
```

---

### 2️⃣ Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 4️⃣ Set Environment Variables

Create a `.env` file in root directory:

```
OPENROUTER_API_KEY="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"
```

---

### 5️⃣ Apply Migrations

```
python manage.py migrate
```

---

### 6️⃣ Run Server

```
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---

## 🌍 Deployment (Render)

### Build Command

```
pip install -r requirements.txt
```

### Start Command

```
cd mentalhealth_project && gunicorn mentalhealth_project.wsgi:application
```

---

## 🔐 Security Notes

* API keys are stored using environment variables
* `.env` file is excluded via `.gitignore`
* Never expose API keys in code
* Always use environment variables in production

---

## ⚠️ Limitations

* No real-time streaming responses (currently reload-based)
* Limited conversation memory
* Basic mobile responsiveness
* Free hosting may sleep after inactivity

---

## 🔮 Future Enhancements

* ⚡ Real-time chat (no page reload)
* 🧠 Advanced conversation memory
* 📱 Fully responsive mobile UI
* 🔍 Chat search functionality
* 📊 User analytics dashboard
* 🌐 Multi-language support

---

## 🧠 Learning Outcomes

Through this project, I learned:

* Full-stack web development using Django
* Integrating Large Language Model APIs
* Designing user authentication systems
* Managing chat-based data models
* Building clean UI/UX inspired by real products
* Deploying applications using Render
* Handling API errors and fallbacks

---


## 👨‍💻 Author

**Vinay Venkata Bhargav**

GitHub: https://github.com/bhargav20-ui

---

## ⭐ Support

If you found this project useful:

* ⭐ Star this repository
* 🔗 Share it with others
* 💬 Give feedback

---

## 💬 Final Note

This project is a step towards building intelligent, human-centered AI applications that support mental well-being in a simple, accessible, and meaningful way.
