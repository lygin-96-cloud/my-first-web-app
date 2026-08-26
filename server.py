from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-key-12345'

# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- НАСТРОЙКА АВТОРИЗАЦИИ ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- TELEGRAM НАСТРОЙКИ ---
BOT_TOKEN = "ТВОЙ_ТОКЕН"        # 👈 замени
CHAT_ID = "ТВОЙ_CHAT_ID"        # 👈 замени

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

# --- МОДЕЛИ БАЗЫ ДАННЫХ ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Новый')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.String(50))
    image_url = db.Column(db.String(300))

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    services = Service.query.all()
    return render_template('index.html', user=current_user, services=services)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Логин занят!', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        
        # 📩 Уведомление в Telegram
        msg = f"🆕 <b>Новый пользователь!</b>\n\n"
        msg += f"👤 Логин: {username}\n"
        msg += f"🕒 Дата: {user.created_at.strftime('%d.%m.%Y %H:%M')}"
        send_telegram_message(msg)
        
        flash('Регистрация успешна! Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user, remember=True)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, orders=orders)

@app.route('/order', methods=['POST'])
@login_required
def order():
    service = request.form['service']
    description = request.form['description']
    order = Order(user_id=current_user.id, service=service, description=description)
    db.session.add(order)
    db.session.commit()
    
    # 📩 Уведомление в Telegram
    msg = f"🆕 <b>Новый заказ!</b>\n\n"
    msg += f"👤 Клиент: {current_user.username}\n"
    msg += f"📦 Услуга: {service}\n"
    msg += f"📝 Описание: {description}\n"
    msg += f"🕒 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    send_telegram_message(msg)
    
    flash('Заказ отправлен!', 'success')
    return redirect(url_for('profile'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        fb = Feedback(name=name, email=email, message=message)
        db.session.add(fb)
        db.session.commit()
        
        # 📩 Уведомление в Telegram
        msg = f"💬 <b>Новое сообщение!</b>\n\n"
        msg += f"👤 Имя: {name}\n"
        msg += f"📧 Email: {email}\n"
        msg += f"📝 Сообщение: {message}\n"
        msg += f"🕒 Дата: {fb.created_at.strftime('%d.%m.%Y %H:%M')}"
        send_telegram_message(msg)
        
        flash('Сообщение отправлено!', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    orders = Order.query.all()
    services = Service.query.all()
    feedbacks = Feedback.query.all()
    return render_template('admin.html', orders=orders, services=services, feedbacks=feedbacks)

@app.route('/admin/add_service', methods=['POST'])
@login_required
def add_service():
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    title = request.form['title']
    description = request.form['description']
    price = request.form['price']
    image_url = request.form['image_url']
    service = Service(title=title, description=description, price=price, image_url=image_url)
    db.session.add(service)
    db.session.commit()
    flash('Услуга добавлена!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_service/<int:id>')
@login_required
def delete_service(id):
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    service = Service.query.get(id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_order/<int:id>')
@login_required
def delete_order(id):
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    order = Order.query.get(id)
    db.session.delete(order)
    db.session.commit()
    flash('Заказ удалён!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/map')
def map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
