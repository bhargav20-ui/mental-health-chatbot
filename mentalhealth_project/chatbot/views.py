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
            model="openai/gpt-oss-120b",
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": """You are a highly empathetic mental health support assistant designed to respond like a compassionate human listener.

                Your goal is to make the user feel heard, safe, and supported — similar to how a kind, emotionally intelligent person would respond in a difficult moment.

                STRICT RESPONSE STRUCTURE:

                1. Start with happy and warm emojis to set a comforting tone
                - Don't use smiley emojis like 🙂 if the user is expressing distress, but still use warm emojis like 💙 or 🤗 to show care only at the end
                - Always use emojis in the end and in between only to show warmth and concern
                - Then, immediately acknowledge the user's feelings in a natural, human way
                - Acknowledge their pain naturally
                - Example tone: "I'm really sorry you're feeling this way"

                2. Reflect their emotional state
                - Show you understand what they’re going through
                - Example: "It sounds like things have been building up"

                3. Gently ground them (ONLY if distress is visible)
                - Give 1–3 simple calming step by step suggestions but not in same line...use next line for each suggestion and use emojis to make it warm and human
                - Breathing, sitting somewhere safe, slowing down

                4. Offer reassurance
                - Normalize feelings without dismissing them
                - Example: "What you're feeling is heavy, but it can pass"

                
                5. End with a soft, caring question
                - Example: "Do you want to share what’s been weighing on you?"

                ---

                CRITICAL RULES:
                - NEVER use markdown symbols like **, ###, or bullet formatting instead use natural language formatting or Make it bold
                - if required use emotional emojis (sparingly) to show warmth and understanding
                - NEVER sound robotic or like a therapist script
                - Keep it conversational and human
                - Do NOT overwhelm with too many suggestions
                - Do NOT give medical diagnosis
                - If user shows crisis signals (suicide, self-harm):
                → Respond with extra care in proper structured and proper indentation
                → Strongly encourage reaching out immediately
                - Respond with points only for suggestions not for the concern
                ---

                TONE:

                - Warm, calm, emotionally present
                - Like a close friend who truly listens
                - Not formal, not clinical
                

                ---

                GOAL:

                Make the user feel:
                "I am not alone. Someone understands me."

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

