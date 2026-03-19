from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

import json
import re
from .models import ChatMessage

# -----------------------------
# OPENROUTER SETUP
# -----------------------------
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"   # 🔐 Replace with your new key
)

# -----------------------------
# CLEAN RESPONSE (REMOVE MARKDOWN)
# -----------------------------

def clean_response(text):
    if not text:
        return "Sorry, I'm having trouble responding right now."

    text = re.sub(r'\*\*', '', text)   # remove **
    text = re.sub(r'#+', '', text)     # remove ###
    text = re.sub(r'\|.*?\|', '', text)

    return text.strip()


# -----------------------------
# LOGIN
# -----------------------------
def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )

        if user:
            login(request, user)
            return redirect('home')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


# -----------------------------
# SIGNUP
# -----------------------------
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'User already exists'})

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('home')

    return render(request, 'signup.html')


# -----------------------------
# HOME
# -----------------------------
@login_required
def home(request):
    messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'home.html', {'messages': messages})


# -----------------------------
# LOGOUT
# -----------------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# -----------------------------
# CHAT API
# -----------------------------
@login_required
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')

        response = get_bot_response(message)

        # ✅ Prevent DB crash
        if not response:
            response = "Sorry, I'm having trouble responding right now."

        ChatMessage.objects.create(
            user=request.user,
            message=message,
            response=response
        )

        return JsonResponse({'response': response})


# -----------------------------
# CHATBOT LOGIC (FINAL)
# -----------------------------
def get_bot_response(message):
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            messages=[
                {
                    "role": "system",
                    "content": "Act like a kind mental health assistant. Give structured, all simple bullet points. Keep it supportive, interactive, and not too long. Avoid markdown symbols like ** or ###. Use natural language."
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        raw_response = completion.choices[0].message.content
        return clean_response(raw_response)

    except Exception as e:
        print("ERROR:", e)

        # 🔥 FALLBACK (VERY IMPORTANT)
        # msg = message.lower()

        # if "sad" in msg:
        #     return "I'm really sorry you're feeling this way 💙 I'm here for you."
        # elif "stress" in msg or "anxiety" in msg:
        #     return "Take a deep breath. You're doing your best."
        # elif "happy" in msg:
        #     return "That's wonderful 😊 I'm glad you're feeling happy!"
        # elif "lonely" in msg:
        #     return "You're not alone 🤝 I'm here with you."
        # else:
        #     return "Tell me more about how you're feeling 💙"