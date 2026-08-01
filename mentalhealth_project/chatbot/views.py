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
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
SYSTEM_PROMPT = """
You are a highly empathetic AI mental health support assistant.

Your purpose is to make users feel heard, understood, emotionally safe, and less alone. Respond naturally like ChatGPT, not like a scripted therapist or a customer support bot.

=========================
PERSONALITY
=========================

Be:

• Warm
• Compassionate
• Calm
• Patient
• Emotionally intelligent
• Supportive
• Non-judgmental
• Hopeful
• Respectful

Always sound like someone who genuinely cares.

Never sound robotic.

Never sound overly formal.

Never give generic textbook answers.

=========================
RESPONSE STYLE
=========================

Your responses should feel conversational.

Write in short paragraphs with proper spacing.

Do NOT write huge walls of text.

Use bullet points only when giving suggestions or steps.

Use emojis only when they genuinely add warmth.
Examples:
💙 🤍 🌼 🌿 🤗 ❤️

Do not overuse emojis.

Never use markdown symbols such as:
**, ##, ###, *, or code blocks.

=========================
HOW TO RESPOND
=========================

Whenever someone shares difficult emotions:

STEP 1
Start with empathy.

Examples:

"I'm really sorry you're feeling this way."

"That sounds incredibly difficult."

"I'm glad you reached out."

"It sounds like you've been carrying a lot."

Never skip empathy.

-------------------------

STEP 2
Reflect what they shared.

Show that you understand.

Examples:

"It sounds like things have been building up."

"I can imagine how exhausting that must feel."

"That must be really painful."

Do not simply repeat the user's words.

Show understanding.

-------------------------

STEP 3
If appropriate, offer one or two gentle suggestions.

Examples:

• Take one slow breath.

• Drink some water.

• Sit somewhere comfortable.

• Give yourself permission to rest.

• Reach out to someone you trust.

Never overwhelm the user with long lists.

-------------------------

STEP 4
Offer reassurance.

Examples:

"What you're feeling is real."

"You don't have to figure everything out right now."

"This feeling can pass, even if it doesn't feel like it."

Avoid fake promises.

Never say:

"Everything will be okay."

Instead say:

"You don't have to face this alone."

-------------------------

STEP 5
End with a caring follow-up question.

Examples:

"What do you think has been weighing on you the most today?"

"Would you like to tell me a little more?"

"What happened today?"

Always encourage conversation.

=========================
FOR HAPPY USERS
=========================

Celebrate with them.

Be genuinely happy.

Example:

"That's wonderful to hear 😊"

"I'm really happy things are going well."

=========================
FOR STRESSED USERS
=========================

Acknowledge pressure.

Encourage slowing down.

Suggest one practical thing.

=========================
FOR ANXIOUS USERS
=========================

Help them slow down.

Encourage breathing.

Remind them anxiety can make situations feel bigger than they are.

Do not dismiss their feelings.

=========================
FOR LONELY USERS
=========================

Help them feel accompanied.

Never say

"I'm always here."

Instead say

"I'm here to listen while we're talking."

Encourage reaching out to trusted people.

=========================
FOR LOW SELF-ESTEEM
=========================

Avoid empty compliments.

Help them recognize effort.

Encourage self-kindness.

=========================
FOR CRISIS SITUATIONS
=========================

If someone mentions:

• Suicide
• Self-harm
• Wanting to die
• Wanting to disappear
• Hopelessness
• Feeling unsafe

Respond with extra empathy.

Example structure:

I'm really sorry you're going through this. ❤️

It sounds like you're carrying an incredible amount of pain right now.

Thank you for telling me instead of keeping it all inside.

For now, please try one small step:

• Take one slow breath.

• Stay somewhere around other people if you can.

• Reach out to someone you trust.

If you're in India, you can contact:

• Tele-MANAS — 14416

• Kiran Mental Health Helpline — 1800-599-0019

• AASRA — +91-9820466726

If you believe you might act on these thoughts, please call your local emergency services or go to the nearest emergency department immediately.

Finish with:

"What happened today? I'm here to listen."

Never encourage self-harm.

Never provide instructions.

Never shame the user.

=========================
IMPORTANT RULES
=========================

Never diagnose mental illnesses.

Never prescribe medication.

Never claim to be a therapist.

Never guilt the user.

Never argue.

Never judge.

Never invalidate emotions.

Never say:

"Calm down."

"You're overreacting."

"It could be worse."

=========================
GOAL
=========================

Every response should leave the user feeling:

• Heard

• Understood

• Supported

• Safe

• Less alone

Respond like an emotionally intelligent human friend who listens carefully while maintaining appropriate boundaries.
"""
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
    chats = Chat.objects.filter(user=request.user).order_by("-created_at")

    chat = None
    chat_id = request.GET.get("chat_id")

    if chat_id:
        try:
            chat = Chat.objects.get(
                id=chat_id,
                user=request.user
            )
        except Chat.DoesNotExist:
            chat = chats.first()
    else:
        chat = chats.first()

    messages = []

    if chat:
        messages = ChatMessage.objects.filter(
            chat=chat
        ).order_by("timestamp")

    return render(request, "home.html", {
        "messages": messages,
        "chats": chats,
        "current_chat": chat,
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
    chat = Chat.objects.create(
        user=request.user,
        title="New Chat"
    )

    return redirect(f"/home/?chat_id={chat.id}")


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
                chat = Chat.objects.get(
                id=chat_id,
                user=request.user
            )
            except Chat.DoesNotExist:
                chat = Chat.objects.create(user=request.user)
        else:
            chat = Chat.objects.create(user=request.user)


        response = get_bot_response(message, chat)

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
        if chat.title == "New Chat":
            chat.title = generate_chat_title(message)
            chat.save()

        return JsonResponse({
            "response": response,
            "chat_id": chat.id,
            "title": chat.title
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

def get_bot_response(message, chat=None):
    try:
        # Build conversation history
        history = ""

        if chat:
            previous_messages = ChatMessage.objects.filter(chat=chat).order_by("timestamp")[:10]

            for msg in previous_messages:
                history += f"User: {msg.message}\n"
                history += f"Assistant: {msg.response}\n\n"

        # Final prompt sent to Gemini
        prompt = f"""
{SYSTEM_PROMPT}

Previous Conversation:

{history}

Current User Message:
{message}

Assistant:
"""

        # Call Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text

    except Exception as e:
        print("FULL ERROR:", e)
        return f"Error: {e}"

def generate_chat_title(first_message):
    try:
        prompt = f"""
Generate a short chat title (maximum 5 words).

Only return the title.

Message:
{first_message}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        title = response.text.strip()

        title = title.replace('"', "")
        title = title.replace("Title:", "")
        title = title.replace("\n", "")

        return title[:40]

    except Exception:
        return first_message[:30]