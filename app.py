from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  login TEXT UNIQUE, 
                  password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- Главная страница ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Регистрация ---
@app.route('/register', methods=['POST'])
def register():
    login = request.form['login']
    password = request.form['password']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (login, password) VALUES (?, ?)", (login, password))
        conn.commit()
        conn.close()
        return '<h1>Регистрация успешна!</h1><a href="/">Войти</a>'
    except sqlite3.IntegrityError:
        conn.close()
        return '<h1>Такой логин уже существует!</h1><a href="/">Назад</a>'

# --- Вход ---
@app.route('/login', methods=['POST'])
def login():
    login = request.form['login']
    password = request.form['password']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE login=? AND password=?", (login, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return f'<h1>Добро пожаловать, {login}!</h1><a href="/">Выйти</a>'
    else:
        return '<h1>Неверный логин или пароль!</h1><a href="/">Попробовать снова</a>'

if __name__ == '__main__':
    app.run(debug=True, port=8000)