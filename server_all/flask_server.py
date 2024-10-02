from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///photo_reviews.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)
FIXED_SIZE = (360,640)

app.config['STATIC_FOLDER'] = 'static'

class Entry(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    photo_path = db.Column(db.String(200), nullable=False)
    review = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/food_demo')
def server_index():
    return send_from_directory(app.config['STATIC_FOLDER'], 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        name = request.form['name']
        title = request.form['title']
        review = request.form['review']
        rating = int(request.form['rating'])
        photo = request.files['photo']

        if photo:
            filename = secure_filename(photo.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image = Image.open(photo)
            image = ImageOps.exif_transpose(image)
            if image.width > 360 or image.height > 640:
                image.thumbnail(FIXED_SIZE)
            image.save(photo_path)

            entry = Entry(
                id=str(uuid.uuid4()),
                name=name,
                title=title,
                photo_path=unique_filename,
                review=review,
                rating=rating
            )
            db.session.add(entry)
            db.session.commit()

            return jsonify({"message": "Entry created successfully"}), 201
        else:
            return jsonify({"error": "No photo uploaded"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        entries = Entry.query.order_by(Entry.timestamp.desc()).all()
        return jsonify([
            {
                "id": entry.id,
                "name": entry.name,
                "title": entry.title,
                "photo_path": entry.photo_path,
                "review": entry.review,
                "rating": entry.rating,
                "timestamp": entry.timestamp.isoformat()
            } for entry in entries
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/photo/<filename>', methods=['GET'])
def get_photo(filename):
    try:
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0")