from flask import Blueprint, render_template, request, jsonify, url_for, flash, redirect
from flask_login import current_user
from ChatbotWebsite import db
from ChatbotWebsite.chatbot.chatbot import *
from ChatbotWebsite.chatbot.topic import *
from ChatbotWebsite.chatbot.test import *
from ChatbotWebsite.chatbot.mindfulness import *
from ChatbotWebsite.models import ChatMessage
from ChatbotWebsite.chatbot.chatbot import get_response, get_music_by_tag  # add this if not already present


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

# Chat Messages, Post request, get response from chatbot and add both messages to database
@chatbot.route("/chat_messages", methods=["POST"])
def chatting():
    message = request.form["msg"]
    response, tag = get_response(message)
    print(f"predicted tag:{tag}")

    mood_tags = ["feelingsad", "copingwithanger", "sleepissues", "anxiety"]
    tag_lower = tag.lower()
    music_html = ""
    video_html = ""

    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=message, user=current_user)
        db.session.add(user_message)
        db.session.commit()

    if current_user.is_authenticated:
        bot_message = ChatMessage(sender="bot", message=response, user=current_user)
        db.session.add(bot_message)
        db.session.commit()

    if tag_lower in mood_tags:
        music_path = get_music_by_tag(tag_lower)
        if music_path:
            music_html = f'''
            <p><b>You might find this helpful:</b><br>
            Give this a listen, it may help you feel a bit better. 🎵</p>
            <audio controls>
                <source src="{music_path}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            '''

        video_links = {
            "feelingsad": "https://www.youtube.com/watch?v=mgmVOuLgFB0",
            "copingwithanger": "https://www.youtube.com/watch?v=mb9pG-bZlU8",
            "sleepissues": "https://www.youtube.com/watch?v=9HuUtshnOEA",
            "anxiety": "https://www.youtube.com/watch?v=WWloIAQpMcQ",
            "depression":"https://www.youtube.com/watch?v=d96akWDnx0w",
            "suicide":"https://www.youtube.com/watch?v=k9vvAFU9-Q8"

        }

        if tag_lower in video_links:
            video_link = video_links[tag_lower]
            video_html = f'''
            <p><b>Need a little motivation? 🎥</b><br>
            Here's a video that might inspire you:<br>
            <a href="{video_link}" target="_blank">{video_link}</a></p>
            '''

    distress_keywords = ["i am sad", "i am not feeling well", "i can’t sleep", "i feel anxious", "i’m depressed"]
    if not hasattr(chatting, "distress_count"):
        chatting.distress_count = 0

    if any(kw in message.lower() for kw in distress_keywords):
        chatting.distress_count += 1
    
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
        chatting.distress_count = 0

    return jsonify({
        "msg": response,
        "music": music_html,
        "video": video_html,
        "sos": sos_html
    })

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