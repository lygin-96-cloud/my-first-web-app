from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# --- HTML-шаблон (встроенный)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Мой сайт</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 400px;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 10px; }
        h2 { color: #555; font-size: 18px; margin: 20px 0 10px; }
        input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
            transition: 0.3s;
        }
        button:hover { background: #5a67d8; }
        .message {
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        a { color: #667eea; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .logout { margin-top: 20px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        {% if user %}
            <h1>👋 Добро пожаловать, {{ user }}!</h1>
            <p style="margin: 20px 0; color: #555;">Вы успешно вошли в систему.</p>
            <a href="/logout" class="logout" style="color: #dc3545;">Выйти</a>
        {% else %}
            <h1>🚀 Добро пожаловать!</h1>
            
            <h2>Регистрация</h2>
            <form action="/register" method="POST">
                <input type="text" name="username" placeholder="Логин" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Зарегистрироваться</button>
            </form>
            
            <h2>Вход</h2>
            <form action="/login" method="POST">
                <input type="text" name="username" placeholder="Логин" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="message {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        {% endif %}
    </div>
</body>
</html>
'''

# --- Главная страница
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, user=None)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return render_template_string(HTML_TEMPLATE, user=username)
    except sqlite3.IntegrityError:
        return "<h1>Такой логин уже существует!</h1><a href='/'>На главную</a>"
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return render_template_string(HTML_TEMPLATE, user=username)
    else:
        return "<h1>Неверный логин или пароль!</h1><a href='/'>Попробовать снова</a>"

@app.route('/logout')
def logout():
    return redirect('/')

if __name__ == '__main__':
==> Running 'python server.py'
* Running on http://0.0.0.0:8000
