from flask import Blueprint, render_template, request, jsonify, url_for, flash, redirect
from flask_login import current_user
from ChatbotWebsite import db
from ChatbotWebsite.chatbot.chatbot import *
from ChatbotWebsite.chatbot.topic import *
from ChatbotWebsite.chatbot.test import *
from ChatbotWebsite.chatbot.mindfulness import *
from ChatbotWebsite.models import ChatMessage

chatbot = Blueprint("chatbot", __name__)


# Chat Page (Main Page)
@chatbot.route("/chat")
def chat():
    messages = None
    if current_user.is_authenticated:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "chat/chat.html",
        title="Chat",
        topics=topics,
        messages=messages,
        tests=tests,
        mindfulness_exercises=mindfulness_exercises,
    )


# Chat Messages, Post reqeust, get response from chatbot and add both messages to database
@chatbot.route("/chat_messages", methods=["POST"])
def chatting():
    message = request.form["msg"]
    
    # Get response and tag from your chatbot function (make sure get_response returns both)
    response, tag = get_response(message)
    print(f"predicted tag:{tag}")
    
    mood_tags = ["feelingsad", "copingwithanger", "sleepissues", "anxiety"]
    tag_lower = tag.lower()
    music_html=""

    # Save user message first
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=message, user=current_user)
        db.session.add(user_message)
        db.session.commit()

    # Save bot main response message
    if current_user.is_authenticated:
        bot_message = ChatMessage(sender="bot", message=response, user=current_user)
        db.session.add(bot_message)
        db.session.commit()

    # If the tag is in mood_tags, add another message with music player
    if tag_lower in mood_tags:
        music_path = get_music_by_tag(tag_lower)
        if music_path:
            music_html = music_html = f'''
    <p><b>You might find this helpful:</b><br>
    Give this a listen, it may help you feel a bit better. 🎵</p>
    <audio controls>
        <source src="{music_path}" type="audio/mpeg">
        Your browser does not support the audio element.
    </audio>
            '''

     # SOS Message Logic – show after repeated signs of distress
    distress_keywords = ["i am sad", "i am not feeling well", "i can’t sleep", "i feel anxious", "i’m depressed"]
    if not hasattr(chatting, "distress_count"):
        chatting.distress_count = 0

    if any(kw in message.lower() for kw in distress_keywords):
        chatting.distress_count += 1
    print(f"count:{chatting.distress_count}")
    sos_html = ""
    if chatting.distress_count >= 3:
        sos_html = '''
            <p><b>You're not alone ❤️</b><br>
            If you're feeling overwhelmed, it's okay to ask for help. You can contact a mental health professional or reach out through the helplines below:</p>
            <ul>
                <li><b>📞 Mental Health Helpline:</b> 1660-01-34567</li>
                <li><b>📞 Suicide Prevention (Nepal):</b> 1166</li>
                <li><b>🌐 International Lifeline:</b> <a href="https://www.befrienders.org/" target="_blank">www.befrienders.org</a></li>
            </ul>
            <p>
             👉 For more helpline connections, visit: 
             <a href="http://127.0.0.1:5000/sos" target="_blank"> http://127.0.0.1:5000/sos</a>
            </p>
        '''
        chatting.distress_count = 0  # reset counter

    # Save messages
    if current_user.is_authenticated:
        db.session.add(ChatMessage(sender="user", message=message, user=current_user))
        db.session.add(ChatMessage(sender="bot", message=response, user=current_user))
        db.session.commit()

    return jsonify({
        "msg": response,
        "music": music_html,
        "sos": sos_html
    })
            

    # If no music to recommend, just return the bot message
    return jsonify({"msg": response})


# Topic, Post request, get contents from topic and add all messages to database
@chatbot.route("/topic", methods=["POST"])
def topic():
    title = request.form["title"]
    contents = get_content(title)
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=title, user=current_user)
        db.session.add(user_message)
        for content in contents:
            bot_message = ChatMessage(sender="bot", message=content, user=current_user)
            db.session.add(bot_message)
        db.session.commit()
    return jsonify({"contents": contents})


# Test, Post request, get questions from test
@chatbot.route("/test", methods=["POST"])
def test():
    title = request.form["title"]
    questions = get_questions(title)
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=title, user=current_user)
        db.session.add(user_message)
        db.session.commit()
    return jsonify({"questions": questions})


# Test Score, Post request, get score message from test and add result to database
@chatbot.route("/score", methods=["POST"])
def score():
    score = request.form["score"]
    title = request.form["title"]
    score_message = get_test_messages(title, score)
    if current_user.is_authenticated:
        bot_score_message = ChatMessage(
            sender="bot", message=score_message, user=current_user
        )
        db.session.add(bot_score_message)
        db.session.commit()
    return jsonify({"score_message": score_message})


# Mindfulness, Post request, get description, file_name from mindfulness exercise
@chatbot.route("/mindfulness", methods=["POST"])
def mindfulness():
    title = request.form["title"]
    description, file_name = get_description(title)
    return jsonify({"description": description, "file_name": file_name})


def get_music_by_tag(tag):
    music_library = {
        "feelingsad": "/static/music/sad.mp3",
        "copingwithanger": "/static/songs/sad_song.mp3",   
        "anxiety": "/static/songs/depressed_song.mp3",
        "sleepissues": "/static/songs/angry_song.mp3",
    }
    return music_library.get(tag, "")
# "FeelingSad", "CopingWithAnger", "CopingWithAnger","SleepIssues"D:\project III\project cipher\Cipher\ChatbotWebsite\chatbot\static\music\sad.mp3