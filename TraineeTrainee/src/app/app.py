from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    file = request.args.get('filepath')
    if file:
        return open(file).read()
    return render_template('index.html')

app.run(host="0.0.0.0", port=5000)