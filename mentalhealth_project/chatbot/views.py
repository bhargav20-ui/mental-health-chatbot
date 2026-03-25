from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

import json
import re
from .models import ChatMessage, Chat

# -----------------------------
# OPENROUTER SETUP
# -----------------------------
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"   # 🔐 PUT NEW KEY HERE
)

# -----------------------------
# CLEAN RESPONSE
# -----------------------------
def clean_response(text):
    if not text:
        return "Sorry, I'm having trouble responding right now."

    # remove accidental system prompt leak
    if "Role:" in text or "Tone:" in text:
        return "Hey, I'm here for you 😊 Tell me how you're feeling."

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
    chats = Chat.objects.filter(user=request.user).order_by('-created_at')

    chat_id = request.GET.get('chat_id')

    if chat_id:
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            chat = chats.first()
    else:
        chat = chats.first()

    messages = ChatMessage.objects.filter(chat=chat).order_by('timestamp') if chat else []

    return render(request, 'home.html', {
        'messages': messages,
        'chats': chats,
        'current_chat': chat
    })


# -----------------------------
# LOGOUT
# -----------------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# -----------------------------
# NEW CHAT
# -----------------------------
@login_required
def new_chat(request):
    chat = Chat.objects.create(user=request.user)
    return redirect(f'/home/?chat_id={chat.id}')


# -----------------------------
# CHAT API
# -----------------------------
@login_required
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')
        chat_id = data.get('chat_id')

        # ✅ SAFE CHAT FETCH
        if chat_id:
            try:
                chat = Chat.objects.get(id=chat_id)
            except Chat.DoesNotExist:
                chat = Chat.objects.create(user=request.user)
        else:
            chat = Chat.objects.create(user=request.user)

        response = get_bot_response(message)

        if not response:
            response = "Sorry, I'm having trouble responding right now."

        # ✅ SAVE MESSAGE
        ChatMessage.objects.create(
            chat=chat,
            user=request.user,
            message=message,
            response=response
        )

        # ✅ SET TITLE (ONLY FIRST MESSAGE)
        if not chat.title:
            chat.title = message[:40]
            chat.save()

        return JsonResponse({
            'response': response,
            'chat_id': chat.id
        })

#------------------------------
# RENAME CHAT
# ------------------------------
@login_required
def rename_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = data.get("chat_id")
        new_title = data.get("title")

        try:
            chat = Chat.objects.get(id=chat_id, user=request.user)
            chat.title = new_title
            chat.save()
            return JsonResponse({"status": "success"})
        except Chat.DoesNotExist:
            return JsonResponse({"status": "error"})
        
# -----------------------------
# DELETE CHAT
# -----------------------------
@login_required
def delete_chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chat_id = data.get("chat_id")

        try:
            chat = Chat.objects.get(id=chat_id, user=request.user)
            chat.delete()
            return JsonResponse({"status": "deleted"})
        except Chat.DoesNotExist:
            return JsonResponse({"status": "error"})

# -----------------------------
# CHATBOT LOGIC (FINAL)
# -----------------------------
def get_bot_response(message):
    try:
        completion = client.chat.completions.create(
            model="qwen/qwen3-next-80b-a3b-instruct",
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": """You are a compassionate, emotionally intelligent mental health support assistant.

                    Your role is to support users like a caring listener — not a clinical therapist, but someone who understands and helps gently.

                    Core behavior:
                    - Always acknowledge the user's feelings first
                    - Validate emotions without judging or dismissing
                    - Never rush into solutions immediately
                    - Focus on understanding before advising
                    - Keep responses warm, human, and conversational — not robotic or formal
                    - warn users to seek real-world support if they express extreme distress or crisis
                    - warn the user if they ask for medical advice that you are not a doctor and cannot provide diagnosis or treatment
                    - warn the user if they uses language that indicates they may be in crisis (e.g., "I want to end it all", "I can't go on", "I'm so alone", "i am gonna die toady" etc..) to seek immediate help from a trusted person or professional

                    Response structure:
                    1. Start with empathy (e.g., "That sounds really tough", "I hear you")
                    2. Reflect their feeling (e.g., "It seems like you're feeling overwhelmed")
                    3. Offer 1–2 gentle suggestions only if appropriate
                    4. End with a soft, open-ended question

                    Important rules:
                    - Never sound robotic, formal, or like a textbook
                    - Never use bullet points or structured lists
                    - Keep responses natural and conversational
                    - Avoid over-advising or overwhelming the user
                    - Do NOT act like a licensed therapist or give medical diagnosis

                    Safety rules:
                    - If user expresses extreme distress, loneliness, or crisis:
                    → Respond with extra care and encourage seeking real-world support
                    → Example: "You don’t have to go through this alone. Talking to someone you trust could really help."

                    Tone:
                    - Warm, calm, human, patient
                    - Use simple language
                    - Use emojis rarely (💙) for warmth

                    Goal:
                    Make the user feel heard, safe, and supported enough to continue sharing.
                    """
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
        print("FULL ERROR:", str(e))
        return f"Error: {str(e)}"

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

