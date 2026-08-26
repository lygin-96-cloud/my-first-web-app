from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>MYSTUDIO</title></head>
<body>
    <h1>🚀 Сайт работает!</h1>
    <p>Новая версия загружена {{ time }}</p>
    <a href="/admin">Админка</a>
</body>
</html>
"""

@app.route('/')
def index():
    from datetime import datetime
    return render_template_string(HTML, time=datetime.now())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)