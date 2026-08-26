from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import os

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

# --- HTML-шаблон (главная страница)
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
        a { color: #667eea; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .logout { margin-top: 20px; display: inline-block; color: #dc3545; }
        .admin-link { margin-top: 20px; display: inline-block; color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        {% if user %}
            <h1>👋 Добро пожаловать, {{ user }}!</h1>
            <p style="margin: 20px 0; color: #555;">Вы успешно вошли в систему.</p>
            <a href="/logout" class="logout">Выйти</a><br>
            <a href="/admin" class="admin-link">🔐 Админ-панель</a>
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
        {% endif %}
    </div>
</body>
</html>
'''

# --- Админ-панель (список пользователей)
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Админ-панель</title>
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
            width: 600px;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 20px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th { background: #667eea; color: white; }
        a { color: #667eea; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .back { margin-top: 20px; display: inline-block; }
        .error { color: red; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>👑 Админ-панель</h1>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        <form action="/admin" method="POST">
            <input type="password" name="admin_password" placeholder="Введите секретный пароль" style="width: 100%;">
            <button type="submit">Войти в админку</button>
        </form>
        
        {% if users %}
            <h2>📋 Список пользователей</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Логин</th>
                    <th>Пароль</th>
                </tr>
                {% for user in users %}
                <tr>
                    <td>{{ user[0] }}</td>
                    <td>{{ user[1] }}</td>
                    <td>{{ user[2] }}</td>
                </tr>
                {% endfor %}
            </table>
        {% endif %}
        
        <a href="/" class="back">← На главную</a>
    </div>
</body>
</html>
'''

# --- Маршруты

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

# --- Админ-панель
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        admin_password = request.form.get('admin_password')
        # Секретный пароль для входа в админку (можешь изменить)
        if admin_password == 'admin123':
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users")
            users = c.fetchall()
            conn.close()
            return render_template_string(ADMIN_TEMPLATE, users=users, error=None)
        else:
            return render_template_string(ADMIN_TEMPLATE, users=None, error='❌ Неверный пароль!')
    
    # GET-запрос — показываем форму входа
    return render_template_string(ADMIN_TEMPLATE, users=None, error=None)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
