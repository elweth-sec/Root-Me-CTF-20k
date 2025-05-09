from flask import Flask, render_template, request, redirect, url_for
import subprocess
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        if pseudo:
            try:
                subprocess.run(['badge-creator', pseudo], timeout=8)
            except subprocess.TimeoutExpired:
                return render_template('index.html', sent=True)
            except Exception as e:
                return str(e)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
