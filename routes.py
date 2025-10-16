from bson.objectid import ObjectId
from flask import Blueprint, render_template, request, redirect, jsonify
from . import mongo, mail
from flask_mail import Message
from .models import Event
import re
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def landing():
    return render_template('landing.html')

@main.route('/team')
def team():
    members = mongo.db.team.find()
    return render_template('team.html', members=members)

@main.route('/events')
def events():
    raw_events = mongo.db.events.find().sort("date", 1)
    events = []

    for e in raw_events:
        title = e.get('title', '').strip()
        date = e.get('date', '').strip()
        location = e.get('location', '').strip()

        if not title or not date or not location:
            continue

        events.append({
            '_id': str(e['_id']),
            'title': title,
            'date': date,
            'location': location,
            'description': e.get('description', '').strip()
        })

    return render_template('events.html', events=events)

@main.route('/events/<event_id>', methods=['GET', 'POST'])
def event_detail(event_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    comments = list(mongo.db.comments.find({"event_id": str(event_id)}).sort("timestamp", -1))

    if request.method == 'POST':
        if 'reply_to' in request.form:
            parent_id = ObjectId(request.form['reply_to'])
            reply = {
                "name": request.form.get('name', '').strip(),
                "reply": request.form.get('reply', '').strip(),
                "timestamp": datetime.utcnow()
            }
            mongo.db.comments.update_one(
                {"_id": parent_id},
                {"$push": {"replies": reply}}
            )
        else:
            name = request.form.get('name', '').strip()
            comment = request.form.get('comment', '').strip()
            if name and comment:
                mongo.db.comments.insert_one({
                    "event_id": str(event_id),
                    "name": name,
                    "comment": comment,
                    "timestamp": datetime.utcnow(),
                    "replies": []
                })

        return redirect(f'/events/{event_id}')

    return render_template('event_detail.html', event=event, comments=comments)

@main.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        data = {k: request.form.get(k, '').strip() for k in ['title', 'date', 'location', 'description', 'email']}
        if not all(data.values()):
            return "All fields are required.", 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            return "Invalid email address.", 400
        if data['title'].lower() == 'untitled event':
            return "Please provide a meaningful event title.", 400

        event = Event(**data)
        mongo.db.events.insert_one(event.to_dict())

        msg = Message("Event Confirmation", recipients=[event.email])
        msg.body = f"You're confirmed for {event.title}!"

        try:
            mail.send(msg)
        except Exception as e:
            return f"Failed to send email: {str(e)}", 500

        return redirect('/events')

    return render_template('create.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        selected_event = request.form.get('event', '').strip()

        if not name or not email or not selected_event:
            return "All fields are required.", 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email address.", 400

        mongo.db.registrations.insert_one({
            "name": name,
            "email": email,
            "event": selected_event
        })

        msg = Message("GDG Event Registration", recipients=[email])
        msg.body = f"Hi {name}, you're registered for {selected_event}!"
        try:
            mail.send(msg)
        except Exception as e:
            return f"Failed to send confirmation email: {str(e)}", 500

        return redirect('/events')

    return render_template('register.html')

@main.route('/events/cleanup/untitled', methods=['POST'])
def cleanup_untitled_events():
    try:
        deletion_filter = {
            "$or": [
                {"title": {"$exists": False}},
                {"title": None},
                {"title": {"$type": "string", "$eq": ""}},
                {"title": "Untitled Event"}
            ]
        }

        result = mongo.db.events.delete_many(deletion_filter)

        return jsonify({
            "deleted_count": result.deleted_count,
            "message": "Untitled events removed successfully."
        }), 200

    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500
