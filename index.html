from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)

# --- Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# --- Главная страница с формами
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Регистрация и вход</title>
        <style>
            body { font-family: Arial; text-align: center; margin-top: 50px; }
            form { display: inline-block; text-align: left; margin: 10px; }
            input { display: block; margin: 10px 0; padding: 8px; width: 200px; }
            button { padding: 8px 20px; }
        </style>
    </head>
    <body>
        <h1>Добро пожаловать!</h1>
        
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
    </body>
    </html>
    ''')

# --- Обработка регистрации
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return f"<h1>Пользователь {username} зарегистрирован!</h1><a href='/'>На главную</a>"
    except sqlite3.IntegrityError:
        return "<h1>Такой логин уже существует!</h1><a href='/'>Назад</a>"
    finally:
        conn.close()

# --- Обработка входа
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
        return f"<h1>Добро пожаловать, {username}!</h1><a href='/'>Выйти</a>"
    else:
        return "<h1>Неверный логин или пароль!</h1><a href='/'>Попробовать снова</a>"

if __name__ == '__main__':
    app.run(debug=True, port=8000)