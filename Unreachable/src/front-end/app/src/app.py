from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
import requests, jwt, os

app = Flask(__name__)
app.secret_key = os.urandom(30)

API_URL = "http://backend_flask:5000/api"

def generate_token(label, value):
    payload = {label: value}
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token

def verify_token(token, return_value):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload[return_value]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/')
def index():
    token = request.cookies.get('token')
    if token:
        user_id = verify_token(token, 'user_id')
        if user_id:
            return redirect(url_for('notes'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post(f"{API_URL}/login", json={'username': username, 'password': password})
        if response.status_code == 200:
            user_id = response.json().get('user_id')
            if username == "admin":
                resp = make_response(render_template('pin.html'))
                resp.set_cookie('tmp_token', generate_token('username', username), httponly=True)
                return resp
            else:
                resp = make_response(redirect(url_for('notes')))
                resp.set_cookie('token', generate_token('user_id', user_id), httponly=True)
                return resp
        else:
            return render_template('login.html', message='Invalid username or password.')
    return render_template('login.html')

@app.route('/pin', methods=['POST'])
def pin():
    tmp_token = request.cookies.get('tmp_token')
    if not tmp_token:
        return redirect(url_for('index'))
    
    pin = request.form['pin']
    username = verify_token(tmp_token, 'username')
    if username == "admin" and requests.get(f"{API_URL}/pin/{pin}/verify").status_code == 200:
        resp = make_response(redirect(url_for('notes')))
        resp.set_cookie('token', generate_token('user_id', 1), httponly=True)
        resp.delete_cookie('tmp_token')
        return resp
    return render_template('pin.html', message='Invalid PIN')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post(f"{API_URL}/signup", json={'username': username, 'password': password})
        if response.status_code == 201:
            return redirect(url_for('login'))
        elif response.status_code == 400:
            return render_template('register.html', message='Username already taken.')
        else:
            return render_template('register.html', message='Registration failed. Please try again.')
    return render_template('register.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('token')
    return resp

@app.route('/notes')
def notes():
    token = request.cookies.get('token')
    if token:
        user_id = verify_token(token, 'user_id')
        if user_id:
            response = requests.get(f"{API_URL}/notes/?user_id={int(user_id)}")
            if response.status_code == 200:
                notes = response.json()
                return render_template('notes.html', notes=notes, user_id=user_id)
            else:
                return render_template('notes.html')
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/note/<note_id>/show', methods=['GET'])
def get_note_by_uuid(note_id):
    response = requests.get(f"{API_URL}/notes/public/{note_id}")

    if response.status_code == 200:
        notes = response.json()
        return render_template('share_note.html', notes=notes)
    else:
        return render_template('error.html', message="This note is not public.")

@app.route('/submit_note', methods=['POST'])
def submit_note():
    token = request.cookies.get('token')
    if token:
        user_id = verify_token(token, 'user_id')
        if user_id:
            title = request.form['title']
            content = request.form['content']
            public = request.form.get('public', 'off') == 'on'

            response = requests.post(f"{API_URL}/notes", json={'title': title, 'content': content, 'public': public, 'user_id': user_id})
            if response.status_code == 201:
                return redirect(url_for('notes'))
            else:
                return "Failed to submit note."
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/admin', methods=['GET'])
def admin():
    token = request.cookies.get('token')
    if token:
        user_id = verify_token(token, 'user_id')
        if user_id == 1:
            try:
                response = requests.get(f"{API_URL}/public_notes")
                if response.status_code == 200:
                    notes = response.json()
                    return render_template('admin.html', notes=notes)
                else:
                    return render_template('error.html', message='Failed to fetch public notes from backend'), 500
            except requests.exceptions.RequestException as e:
                return render_template('error.html', message='Failed to connect to backend server'), 500
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/admin/export/<id>', methods=['GET'])
def export(id):
    token = request.cookies.get('token')
    if token:
        user_id = verify_token(token, 'user_id')
        if user_id == 1:
            try:
                response = requests.post(f"{API_URL}/generate_pdf", json={'id_note': id})
                if response.status_code == 200:
                    pdf_base64 = response.json()['pdf_base64']
                    return render_template('display_pdf.html', pdf_base64=pdf_base64)
                else:
                    return render_template('error.html', message='Failed to generate PDF'), 500
            except requests.exceptions.RequestException as e:
                return render_template('error.html', message='Failed to connect to backend server'), 500
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)