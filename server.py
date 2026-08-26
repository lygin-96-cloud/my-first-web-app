from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os
import re  # Для проверки email
import smtplib
from email.mime.text import MIMEText
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ===== НАСТРОЙКИ ПОЧТЫ (ИЗМЕНИ ПОД СЕБЯ) =====
EMAIL_SENDER = "твоя_почта@gmail.com"      # Твоя почта
EMAIL_PASSWORD = "твой_пароль_приложения"  # Пароль приложения (не обычный)
SMTP_SERVER = "smtp.gmail.com"             # Для Gmail
SMTP_PORT = 587

# ===== ФУНКЦИЯ ОТПРАВКИ ПИСЬМА =====
def send_verification_email(to_email, username, token):
    link = f"https://my-first-web-app-hiif.onrender.com/confirm/{token}"
    subject = "Подтверждение регистрации"
    body = f"""
    Привет, {username}!
    
    Подтверди свою почту, перейдя по ссылке:
    {link}
    
    Если ты не регистрировался, проигнорируй это письмо.
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Ошибка отправки:", e)
        return False

# ===== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (С ПОЛЕМ "ПОДТВЕРЖДЁН") =====
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Таблица пользователей (добавлены поля email, token, confirmed)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        token TEXT,
        confirmed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица заказов (оставляем)
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_phone TEXT,
        service_type TEXT,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Новый'
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ===== ГЛАВНАЯ СТРАНИЦА =====
@app.route('/')
def index():
    return render_template_string(PAGE_TEMPLATE, user=None)

# ===== РЕГИСТРАЦИЯ С ПРОВЕРКОЙ EMAIL =====
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    # Проверка, что email корректный
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return "<h1>❌ Введите корректный email!</h1><a href='/'>Назад</a>"
    
    # Проверка, что логин не содержит пробелов
    if ' ' in username:
        return "<h1>❌ Логин не должен содержать пробелов!</h1><a href='/'>Назад</a>"
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        token = secrets.token_urlsafe(32)
        c.execute("INSERT INTO users (username, password, email, token, confirmed) VALUES (?, ?, ?, ?, 0)", 
                  (username, password, email, token))
        conn.commit()
        conn.close()
        
        # Отправка письма с подтверждением
        send_verification_email(email, username, token)
        
        return f"""
        <h1>✅ Регистрация почти завершена!</h1>
        <p>На почту {email} отправлено письмо с ссылкой для подтверждения.</p>
        <p>Перейди по ссылке, чтобы активировать аккаунт.</p>
        <a href='/'>На главную</a>
        """
    except sqlite3.IntegrityError:
        conn.close()
        return "<h1>❌ Логин или почта уже заняты!</h1><a href='/'>Назад</a>"

# ===== ПОДТВЕРЖДЕНИЕ ПОЧТЫ =====
@app.route('/confirm/<token>')
def confirm_email(token):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE token=? AND confirmed=0", (token,))
    user = c.fetchone()
    
    if user:
        c.execute("UPDATE users SET confirmed=1, token=NULL WHERE id=?", (user[0],))
        conn.commit()
        conn.close()
        return """
        <h1>✅ Почта подтверждена!</h1>
        <p>Теперь ты можешь войти в свой аккаунт.</p>
        <a href='/'>Войти</a>
        """
    else:
        conn.close()
        return """
        <h1>❌ Ссылка недействительна или аккаунт уже активирован.</h1>
        <a href='/'>На главную</a>
        """

# ===== ВХОД (только для подтверждённых) =====
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND confirmed=1", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return render_template_string(PAGE_TEMPLATE, user=username)
    else:
        return "<h1>❌ Неверный логин/пароль или почта не подтверждена!</h1><a href='/'>Попробовать снова</a>"

# ===== ОСТАЛЬНЫЕ МАРШРУТЫ (заказы, админка) =====
# ... (оставляем всё как было в прошлом коде, кроме logout)

@app.route('/logout')
def logout():
    return redirect('/')

@app.route('/place-order', methods=['POST'])
def place_order():
    service = request.form['service']
    name = request.form['customer_name']
    phone = request.form['customer_phone']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (customer_name, customer_phone, service_type) VALUES (?, ?, ?)", 
              (name, phone, service))
    conn.commit()
    conn.close()
    
    return """
    <h1>✅ Заказ принят!</h1>
    <p>Скоро с вами свяжутся.</p>
    <a href='/'>На главную</a>
    """

@app.route('/orders')
def orders():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY order_date DESC")
    all_orders = c.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Заказы</title>
        <style>
            body { font-family: Arial; background: #f0f2f5; padding: 40px; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 20px; }
            h1 { color: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #667eea; color: white; padding: 12px; text-align: left; }
            td { padding: 12px; border-bottom: 1px solid #eee; }
            .badge { background: #ffc107; padding: 4px 12px; border-radius: 20px; }
            a { color: #667eea; text-decoration: none; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Заказы</h1>
            <table>
                <tr><th>ID</th><th>Услуга</th><th>Клиент</th><th>Телефон</th><th>Дата</th><th>Статус</th></tr>
    '''
    for order in all_orders:
        html += f'''
        <tr>
            <td>{order[0]}</td>
            <td>{order[3]}</td>
            <td>{order[1]}</td>
            <td>{order[2]}</td>
            <td>{order[4][:16]}</td>
            <td><span class="badge">{order[5]}</span></td>
        </tr>
        '''
    html += '''
            </table>
            <a href="/">← На главную</a>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/admin')
def admin():
    return redirect('/orders')

# ===== HTML-Шаблон (с полем email) =====
PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Моя студия услуг</title>
    <style>
        /* ... весь стиль из прошлого кода ... */
        /* Я сократил для читаемости, но ты можешь вставить полный стиль из предыдущего сообщения */
        body { font-family: Arial; background: #f0f2f5; }
        .navbar { background: white; padding: 15px 50px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: flex; justify-content: space-between; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        .services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; }
        .service-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); text-align: center; }
        .service-card button { background: #667eea; color: white; border: none; padding: 12px 30px; border-radius: 30px; cursor: pointer; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; }
        .modal-content { background: white; padding: 40px; border-radius: 20px; width: 400px; }
        .close { float: right; font-size: 24px; cursor: pointer; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 10px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 10px; cursor: pointer; }
    </style>
</head>
<body>
<div class="navbar">
    <h1>🚀 Моя студия</h1>
    <div>
        {% if user %}
            <span>👋 {{ user }}</span>
            <a href="/orders">📋 Заказы</a>
            <a href="/admin">🔐 Админ</a>
            <a href="/logout">Выйти</a>
        {% else %}
            <a href="#register">Регистрация</a>
            <a href="#login">Вход</a>
        {% endif %}
    </div>
</div>

<div class="container">
    <div class="hero" style="text-align:center; padding:40px 0;">
        <h1 style="font-size:48px;">🔥 Профессиональные услуги</h1>
        <p style="font-size:20px; color:#666;">Выбери свой тариф и закажи прямо сейчас</p>
    </div>

    <div class="services-grid">
        <div class="service-card">
            <h3>📱 SMM-продвижение</h3>
            <p>Настройка рекламы в Instagram, VK, Telegram</p>
            <div class="price" style="color:#667eea; font-size:28px; font-weight:bold;">15 000 ₽</div>
            <button onclick="openOrder('SMM-продвижение')">Заказать</button>
        </div>
        <div class="service-card">
            <h3>🌐 Сайт под ключ</h3>
            <p>Создам сайт от визитки до интернет-магазина</p>
            <div class="price" style="color:#667eea; font-size:28px; font-weight:bold;">от 30 000 ₽</div>
            <button onclick="openOrder('Сайт под ключ')">Заказать</button>
        </div>
        <div class="service-card">
            <h3>🎨 Дизайн-проект</h3>
            <p>Разработка дизайна для бренда, логотип, айдентика</p>
            <div class="price" style="color:#667eea; font-size:28px; font-weight:bold;">10 000 ₽</div>
            <button onclick="openOrder('Дизайн-проект')">Заказать</button>
        </div>
    </div>

    {% if not user %}
    <div style="max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 20px;">
        <h2 id="register">Регистрация</h2>
        <form action="/register" method="POST">
            <input type="text" name="username" placeholder="Логин" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Зарегистрироваться</button>
        </form>
        <h2 id="login">Вход</h2>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="Логин" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
    </div>
    {% endif %}
</div>

<div id="orderModal" class="modal">
    <div class="modal-content">
        <span class="close" onclick="closeOrder()">×</span>
        <h2>📝 Оформление заказа</h2>
        <form action="/place-order" method="POST">
            <input type="text" name="service" id="selectedService" readonly style="background:#f0f2f5;">
            <input type="text" name="customer_name" placeholder="Ваше имя" required>
            <input type="text" name="customer_phone" placeholder="Телефон" required>
            <button type="submit">Отправить заявку</button>
        </form>
    </div>
</div>

<script>
    function openOrder(service) {
        document.getElementById('selectedService').value = service;
        document.getElementById('orderModal').style.display = 'flex';
    }
    function closeOrder() {
        document.getElementById('orderModal').style.display = 'none';
    }
    window.onclick = function(event) {
        let modal = document.getElementById('orderModal');
        if (event.target == modal) modal.style.display = 'none';
    }
</script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
