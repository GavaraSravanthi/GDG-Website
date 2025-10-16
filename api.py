print("api.py loaded")

from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from . import mongo, mail
from flask_mail import Message
from .models import Event
import re

api = Blueprint('api', __name__)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@api.route('/api/events', methods=['GET'])
def get_events():
    events = mongo.db.events.find()
    result = []

    for e in events:
        title = e.get('title', '').strip()
        date = e.get('date', '').strip()
        location = e.get('location', '').strip()

        if not title or not date or not location:
            continue

        result.append({
            '_id': str(e['_id']),
            'title': title,
            'date': date,
            'location': location
        })

    return jsonify(result), 200

@api.route('/api/events/<id>', methods=['GET'])
def get_event(id):
    event = mongo.db.events.find_one({'_id': ObjectId(id)})
    if event:
        event['_id'] = str(event['_id'])
        return jsonify(event), 200
    return jsonify({'error': 'Event not found'}), 404

@api.route('/api/events', methods=['POST'])
def create_event():
    fields = ['title', 'date', 'location', 'description', 'email']
    data = {k: request.form.get(k, '').strip() for k in fields}

    for key, value in data.items():
        if not value:
            return jsonify({'error': f'{key.capitalize()} cannot be empty'}), 400

    if not is_valid_email(data['email']):
        return jsonify({'error': 'Invalid email address'}), 400

    event = Event(**data)
    result = mongo.db.events.insert_one(event.to_dict())

    msg = Message("Event Confirmation", recipients=[event.email])
    msg.body = f"You're confirmed for {event.title}!"

    try:
        mail.send(msg)
    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500

    return jsonify({'message': 'Event created', 'id': str(result.inserted_id)}), 201

@api.route('/api/events/<id>', methods=['PUT'])
def update_event(id):
    data = request.json or {}
    update_fields = {}

    for k in ['title', 'date', 'location', 'description']:
        value = data.get(k, '').strip()
        if value:
            update_fields[k] = value

    if not update_fields:
        return jsonify({'error': 'No valid fields to update'}), 400

    result = mongo.db.events.update_one({'_id': ObjectId(id)}, {'$set': update_fields})
    if result.matched_count:
        return jsonify({'message': 'Event updated'}), 200
    return jsonify({'error': 'Event not found'}), 404

@api.route('/api/events/<id>', methods=['DELETE'])
def delete_event(id):
    result = mongo.db.events.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 1:
        return jsonify({'message': 'Event deleted'}), 200
    return jsonify({'error': 'Event not found'}), 404

@api.route('/api/events/cleanup/untitled', methods=['DELETE'])
def delete_untitled_events():
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