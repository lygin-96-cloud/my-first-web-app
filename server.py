from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- ИНИЦИАЛИЗАЦИЯ БАЗ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
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

# --- HTML-ШАБЛОН (ТОТ ЖЕ, ЧТО Я ДАЛ В ПРОШЛЫЙ РАЗ) ---
PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Моя студия услуг</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            min-height: 100vh;
        }
        .navbar {
            background: white;
            padding: 15px 50px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar h1 { color: #667eea; font-size: 24px; }
        .navbar a {
            color: #333;
            text-decoration: none;
            margin-left: 20px;
            padding: 8px 15px;
            border-radius: 8px;
            transition: 0.3s;
        }
        .navbar a:hover { background: #667eea; color: white; }
        .navbar .btn-logout { color: #dc3545; }
        .navbar .btn-logout:hover { background: #dc3545; color: white; }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .hero {
            text-align: center;
            padding: 40px 0;
        }
        .hero h1 { font-size: 48px; color: #333; }
        .hero p { font-size: 20px; color: #666; margin-top: 10px; }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        .service-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            transition: 0.3s;
            text-align: center;
        }
        .service-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.2);
        }
        .service-card h3 { color: #333; font-size: 22px; }
        .service-card p { color: #666; margin: 15px 0; }
        .service-card .price { 
            color: #667eea; 
            font-size: 28px; 
            font-weight: bold; 
        }
        .service-card button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 30px;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
            margin-top: 15px;
        }
        .service-card button:hover {
            background: #5a67d8;
            transform: scale(1.05);
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            padding: 40px;
            border-radius: 20px;
            width: 400px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-content h2 { margin-bottom: 20px; color: #333; }
        .modal-content input, .modal-content select {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 10px;
        }
        .modal-content button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
        }
        .modal-content button:hover { background: #5a67d8; }
        .close {
            float: right;
            font-size: 24px;
            cursor: pointer;
        }
        .flash-message {
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .flash-error { background: #f8d7da; color: #721c24; }
        .flash-success { background: #d4edda; color: #155724; }
        @media (max-width: 768px) {
            .navbar { flex-direction: column; padding: 15px; }
            .hero h1 { font-size: 32px; }
            .container { padding: 20px 15px; }
            .modal-content { width: 90%; margin: 20px; }
        }
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
            <a href="/logout" class="btn-logout">Выйти</a>
        {% else %}
            <a href="#register">Регистрация</a>
            <a href="#login">Вход</a>
        {% endif %}
    </div>
</div>

<div class="container">
    <div class="hero">
        <h1>🔥 Профессиональные услуги</h1>
        <p>Выбери свой тариф и закажи прямо сейчас</p>
    </div>

    <div class="services-grid">
        <div class="service-card">
            <h3>📱 SMM-продвижение</h3>
            <p>Настройка рекламы в Instagram, VK, Telegram</p>
            <div class="price">15 000 ₽</div>
            <button onclick="openOrder('SMM-продвижение')">Заказать</button>
        </div>
        <div class="service-card">
            <h3>🌐 Сайт под ключ</h3>
            <p>Создам сайт от визитки до интернет-магазина</p>
            <div class="price">от 30 000 ₽</div>
            <button onclick="openOrder('Сайт под ключ')">Заказать</button>
        </div>
        <div class="service-card">
            <h3>🎨 Дизайн-проект</h3>
            <p>Разработка дизайна для бренда, логотип, айдентика</p>
            <div class="price">10 000 ₽</div>
            <button onclick="openOrder('Дизайн-проект')">Заказать</button>
        </div>
    </div>

    {% if not user %}
    <div style="max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 20px;">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <h2 id="register">Регистрация</h2>
        <form action="/register" method="POST">
            <input type="text" name="username" placeholder="Логин" required>
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

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    user = request.args.get('user')
    return render_template_string(PAGE_TEMPLATE, user=user)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return redirect('/?user=' + username)
    except sqlite3.IntegrityError:
        flash('Такой логин уже существует!', 'error')
        return redirect('/')
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
        return redirect('/?user=' + username)
    else:
        flash('Неверный логин или пароль!', 'error')
        return redirect('/')

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
