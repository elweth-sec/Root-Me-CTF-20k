# Unreachable

## Challenge

>   This interface allow users to create notes and share them with friends.
>
>   What could go wrong ?
>
>   Author : `Elweth` 

- Category: Web
- Difficulty: Hard

## Deployment

- Docker compose

```bash
cd src; docker compose up
``` 

## Writeup

Before looking at the source code, we'll take a look at the application as a whole, which is fairly minimalist:
- create an account,
- log in,
- create notes, private or public, and share them.

On this challenge the source code is given, it includes : 
- 1 front-end server that manages authentication and relays requests to the backend,
- 1 back-end server which stores data (users, notes etc)
- 1 nginx server.

Looking at the application code as a whole, it's easy to see that the front-end server simply acts as a “back for front”, relaying requests to the back-end server, which returns the data.

We also know that the admin store it's own password in the application as it's really secure, and he got 2FA on his account :

```python
# Backend
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
```

The back-end application is not directly exposed, and we can communicate only with the front-end.

Using the application, when we create a public note it give the following URL: 

- http://node1.challenges.ctf20k.root-me.org:29650/note/9c6cc232-1812-43d0-8f6e-a68ad080520c/show

The code related to this endpoint is the following :

```python
# Frontend
API_URL = "http://backend_flask:5000/api"
...
@app.route('/note/<note_id>/show', methods=['GET'])
def get_note_by_uuid(note_id):
    response = requests.get(f"{API_URL}/notes/public/{note_id}")

    if response.status_code == 200:
        notes = response.json()
        return render_template('share_note.html', notes=notes)
    else:
        return render_template('error.html', message="This note is not public.")
```

It reach the following code in the back-end application : 

```python
# Backend
@app.route('/api/notes/public/<note_id>', methods=['GET'])
def get_public_note(note_id):
    note = Note.query.filter_by(id=note_id, public=True).first()
    if note:
        return jsonify([{'public': note.public, 'id': note.id, 'title': note.title, 'content': note.content}]), 200
    else:
        return jsonify({'message': 'Note not found or not public!'}), 404
```

The UUID is forwarded as URL parameter to the backend : `requests.get(f"{API_URL}/notes/public/{note_id}")` 

At this time, it's recommanded to start the application locally to debug easily.

### Server side parameter pollution

Once the application up locally, we can start to analyse the network communication between front end backend.

If we create a public note here are the requests : 

- Nginx: `/note/06300bb3-f70b-49b1-9f6e-085cada03b9b/show`
- Frontend: `/note/06300bb3-f70b-49b1-9f6e-085cada03b9b/show`
- Backend: `/api/notes/public/06300bb3-f70b-49b1-9f6e-085cada03b9b`

The UUID is forwarded from back to front as URL parameter without being sanitized.

As there is no sanitization, we can inject parameter using `%3F` which will automaticly being URL-decoded as `?`.

Knowing this, we can inject new parameter to the backend.

- Nginx: `/note/06300bb3-f70b-49b1-9f6e-085cada03b9b%3Fpolluted=pouetpouet/show`
- Frontend: `/note/06300bb3-f70b-49b1-9f6e-085cada03b9b%3Fpolluted=pouetpouet/show` 
- Backend: `/api/notes/public/06300bb3-f70b-49b1-9f6e-085cada03b9b?polluted=pouetpouet`

Here we injected parameter `?polluted=pouetpouet` to the backend API.

### Server side path traversal using HTTP normalization

We cannot inject `../` to directly do a path traversal in the backend API.

However, for exemple the URL `http://192.168.220.132:5002/note/%2E%2E/show` create the following behaviour :

- Nginx: `/note/%2E%2E/show`               
- Frontend: `/note/../show`
- Backend: `/api/notes/`

Usually a URL ending in `/` is considered as incorrect by Flask, but the application uses the following code to indicate that `/api/foo` and `/api/foo/` are equivalent.

```python
app.url_map.strict_slashes = False
```

So in this case we are able to arbitrarily reach the endpoint `/api/notes/` in the backend.

If we look at the code source of the endpoint we discover the following content : 

```python
# Backend
@app.route('/api/notes', methods=['GET'])
def get_notes():
    user_id = request.args.get('user_id')
    notes = Note.query.filter_by(user_id=user_id).all()
    if notes:
        notes_data = [{'id': note.id, 'title': note.title, 'content': note.content, 'public': note.public} for note in notes]
        return jsonify(notes_data), 200
    else:
        return jsonify({'message': 'No notes found!'}), 404
```

It takes a parameter "user_id" and return the notes of the user. Interesting, isn't it?

### Leak admin note

We can mix SSPP & SSPT to request the endpoint to get the notes of any user. We have to use the path traversal to reach `/api/notes/` and use the parameter pollution to insert `?user_id=1` to leak the password of the admin.

- Nginx: `/note/..%3Fuser_id%3D1/show`               
- Frontend: `/note/..%3Fuser_id=1/show`
- Backend: `/api/notes/?user_id=1`

![unreach5](/images/unreach5.png)

And we get the pass!

![unreach1](/images/unreach1.png)

### 2FA Bypass

We can connect to the admin account using the leaked password, but a 2FA mechanism is implemented on the account :

![unreach2](/images/unreach2.png)

The frontend server take the PIN from the user with a POST request, and use a get request to forward the PIN to the backend : 

```python
# Frontend
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
```

The authentication on the admin account is authorized only if the backend server returns a code 200.

As before, as we control the pin in `{API_URL}/pin/{pin}/verify` without sanitization, we can use SSPP et SSPT to reach an enpoint which return 200 to bypass the 2FA mechanism.

This use case is inspired from this exploit : 

- https://docs.google.com/presentation/d/1N9Ygrpg0Z-1GFDhLMiG3jJV6B_yGqBk8tuRWO1ZicV8/edit#slide=id.g82807e23a8_0_8

If we inject `pin=../?` it will request the endpoint `/api/?/verify` in the backend, which return `200 OK`, needed to bypass the 2FA :

```python
# Backend
@app.route('/api', methods=['GET'])
def up():
    return 'Up', 200
```

And we managed to get a valid token to authenticate!

![unreach3](/images/unreach3.png)

We now have access to the admin dashboard.

The admin got a feature to view all "public" notes, and export them to PDF: 

![unreach4](/images/unreach4.png)


### Arbitrary file read

The process used to export the note as PDF is done by the backend and the code is the following.

It's a standard case to the `Sanitize-then-Modify` vulnerability.

```python
# Backend
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
```

Here the title of note is sanitized in the PDF, but the filename based on the title isn't it: 

```python
note_text = f'/tmp/{note.title.replace("..", "").replace("/", "")}'
...
subprocess.run(['xhtml2pdf', f'/tmp/{note.title}', output_file], check=True)
```

So the title is used to open the content of the name after the PDF generated.

To exploit the vulnerability you have to create a note with title "../../../../etc/passwd" :

![alt text](/images/unreach6.png)

And log as admin to export as PDF :

![alt text](/images/unreach7.png)

And we got the file!

![alt text](/images/unreach8.png)

Repeat the exploit to get /flag.txt.