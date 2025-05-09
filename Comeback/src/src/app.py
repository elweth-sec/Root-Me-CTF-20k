import os
import datetime
import uuid

from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt

from bot import visit

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.urandom(64)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Request(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_uuid = db.Column(db.String(36), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('requests', lazy=True))

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    request_id = db.Column(db.String(36), db.ForeignKey('request.id'), nullable=False)
    request = db.relationship('Request', backref=db.backref('file', uselist=False))

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return render_template('index.html')
    return render_template('index.html', current_user=True)

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    response = redirect(url_for('home'))
    response.set_cookie('access_token', '', expires=0)
    return response

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = jwt.encode({'login': user.username}, app.config['JWT_SECRET_KEY'], algorithm="HS256")

    response = make_response(jsonify({"msg": "Login successful"}))
    response.set_cookie('access_token', access_token, httponly=True, max_age=3600)

    return response

@app.route('/api/requests', methods=['POST'])
def api_submit_request():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return jsonify({"msg": "access_token is missing"}), 401
    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404

        title = request.form['title']
        description = request.form['description']
        file = request.files.get('file')

        new_request = Request(title=title, description=description, user_id=user.id)
        db.session.add(new_request)
        db.session.commit()

        file_uuid = None
        if file:
            filename = secure_filename(file.filename)
            file_uuid = str(uuid.uuid4())
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_uuid)
            file.save(file_path)
            new_file = File(uuid=file_uuid, filename=filename, request_id=new_request.id)
            db.session.add(new_file)
        
        if file_uuid:
            new_request.file_uuid = file_uuid
            db.session.commit()

        return jsonify({"msg": "Request submitted successfully"}), 201
    except Exception as e:
        return jsonify({"msg": str(e)}), 401

@app.route('/api/files/<uuid>', methods=['GET'])
def api_get_file(uuid):
    file = File.query.filter_by(uuid=uuid).first()
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.uuid)
        if os.path.exists(file_path):
            return send_from_directory(
                app.config['UPLOAD_FOLDER'],
                file.uuid,
                as_attachment=True,
                download_name=file.filename
            )
        else:
            return jsonify({"msg": "File not found"}), 404
    else:
        return jsonify({"msg": "File not found"}), 404

@app.route('/api/demande/<uuid>', methods=['GET'])
def api_get_request_by_uuid(uuid):
    access_token = request.cookies.get('access_token')
    if not access_token:
        return jsonify({"msg": "access_token is missing"}), 401
    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404

        req = Request.query.filter_by(id=uuid, user_id=user.id).first()
        if not req:
            return jsonify({"msg": "Request not found or not authorized"}), 404

        request_data = {
            'id': req.id,
            'title': req.title,
            'description': req.description,
            'file_uuid': req.file_uuid
        }
        return jsonify(request_data), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 401

@app.route('/api/demandes', methods=['GET'])
def api_get_requests():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return jsonify({"msg": "access_token is missing"}), 401
    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404

        requests = Request.query.filter_by(user_id=user.id).all()
        request_list = []
        for req in requests:
            request_list.append({
                'id': req.id,
                'title': req.title,
                'description': req.description,
                'file_uuid': req.file_uuid
            })

        return jsonify(request_list), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 401

@app.route('/demandes', methods=['GET'])
def demandes():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return redirect(url_for('login'))
    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return redirect(url_for('login'))

        return render_template('demandes.html', current_user=True)
    except Exception as e:
        return redirect(url_for('login'))

@app.route('/demande', methods=['GET'])
def demande():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return redirect(url_for('login'))
    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return redirect(url_for('login'))

        return render_template('demande.html', current_user=True)
    except Exception as e:
        return redirect(url_for('login'))

@app.route('/remind', methods=['GET'])
def remind():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return redirect(url_for('login'))
    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return redirect(url_for('login'))

        return render_template('remind.html', current_user=True)
    except Exception as e:
        return redirect(url_for('login'))

@app.route('/api/remind', methods=['POST'])
def api_remind():
    access_token = request.cookies.get('access_token')
    if not access_token:
        return jsonify({"msg": "access_token is missing"}), 401

    try:
        decoded_token = jwt.decode(access_token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = decoded_token['login']
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404

        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"msg": "URL is missing"}), 400

        if visit(url):
            return jsonify({"success": "true"}), 200
        else:  
            return jsonify({"error": "An error occured"}), 400

    except Exception as e:
        return jsonify({"msg": str(e)}), 401


#### to setup the user
def create_admin_user():
    admin_username = 'admin'
    if not User.query.filter_by(username=admin_username).first():
        hashed_password = generate_password_hash('W00wwàwàwàw_Omgggggéééééç_So_H44Rd!&!&:O')
        new_admin = User(username=admin_username, password=hashed_password)
        db.session.add(new_admin)
        db.session.commit()

        new_request = Request(
            title="flag",
            description="RM{Holy_sh1t_1_W4s_Sure_T0_Pr3vent_XSS}",
            user_id=new_admin.id
        )
        db.session.add(new_request)
        db.session.commit()
        
        print("Admin user and initial request created.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(host="0.0.0.0", port=5000)
