from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import uuid, string, random, subprocess
import base64, os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.url_map.strict_slashes = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    pin = db.Column(db.String(15))

class Note(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('notes', lazy=True))

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({'message': 'Username already exists!'}), 400

    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({'user_id': user.id}), 200 
    else:
        return jsonify({'message': 'Invalid username or password!'}), 401

@app.route('/api/notes', methods=['POST'])
def manage_notes():
    data = request.get_json()
    title = data['title']
    content = data['content']
    public = data['public']
    user_id = data['user_id']
    note = Note(title=title, content=content, public=public, user_id=user_id)
    db.session.add(note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully!'}), 201


@app.route('/api/notes', methods=['GET'])
def get_notes():
    user_id = request.args.get('user_id')
    notes = Note.query.filter_by(user_id=user_id).all()
    if notes:
        notes_data = [{'id': note.id, 'title': note.title, 'content': note.content, 'public': note.public} for note in notes]
        return jsonify(notes_data), 200
    else:
        return jsonify({'message': 'No notes found!'}), 404

@app.route('/api/notes/public/<note_id>', methods=['GET'])
def get_public_note(note_id):
    note = Note.query.filter_by(id=note_id, public=True).first()
    if note:
        return jsonify([{'public': note.public, 'id': note.id, 'title': note.title, 'content': note.content}]), 200
    else:
        return jsonify({'message': 'Note not found or not public!'}), 404

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_data = [{'id': user.id, 'username': user.username} for user in users]
    return jsonify(user_data), 200

@app.route('/api/pin/<pin>/verify', methods=['GET'])
def get_pin(pin):
    user = User.query.get(1)
    if user and user.pin == pin:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False}), 403

@app.route('/api/public_notes', methods=['GET'])
def get_public_notes():
    admin_user = User.query.filter_by(id=1).first()
    public_notes = Note.query.filter(Note.public == True, Note.user_id != admin_user.id).all()
    if public_notes:
        notes_data = [{'id': note.id, 'title': note.title, 'content': note.content, 'public': note.public} for note in public_notes]
        return jsonify(notes_data), 200
    else:
        return jsonify({'message': 'No public notes found!'}), 404

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    id_note = data['id_note']

    note = Note.query.filter_by(id=id_note, public=True).first()
    print(note)
    if not note:
        return jsonify({'message': 'Note not found or not public!'}), 404

    temp_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    note_text = f'/tmp/{note.title.replace("..", "").replace("/", "")}'
    output_file = f'/tmp/{temp_filename}.pdf'

    try:
        with open(note_text, 'w') as f:
            f.write(f"<h1>{note.title}</h1><p>{note.content}</p>")

        subprocess.run(['xhtml2pdf', f'/tmp/{note.title}', output_file], check=True)

        with open(output_file, 'rb') as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

        return jsonify({'pdf_base64': pdf_base64}), 200

    except subprocess.CalledProcessError as e:
        print(e)
        return jsonify({'message': 'Failed to generate PDF'}), 500

    finally:
        if os.path.exists(note_text):
            os.remove(note_text)
        if os.path.exists(output_file):
            os.remove(output_file)

@app.route('/api', methods=['GET'])
def up():
    return 'Up', 200

def generate_string(x):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(x))
    return password

def create_admin():
    password = generate_string(30)
    pin = generate_string(15)
    hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
    admin = User(username='admin', password=hash_password, pin=pin)
    db.session.add(admin)
    db.session.commit()
    admin_note = Note(title='My App is really secure', content=f"My application is so secure that I save my password in private notes: {password}. Anyway, I've implemented 2FA on my account!", public=False, user_id=admin.id)
    db.session.add(admin_note)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()
        app.run(host="0.0.0.0", port="5000")
