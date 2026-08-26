from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import requests
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.secret_key = 'super-secret-key-12345'

# --- БАЗА ДАННЫХ ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- АВТОРИЗАЦИЯ ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- TELEGRAM НАСТРОЙКИ (замени на свои) ---
BOT_TOKEN = "8619987825:AAFfRaJ-endW8YTZPYgZ3PH8f6geTnZU3Ho"
CHAT_ID = "1099656613"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

# --- МОДЕЛИ БАЗЫ ДАННЫХ ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Новый')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(50))
    image_url = db.Column(db.String(300))

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    link = db.Column(db.String(300))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- СОЗДАНИЕ БАЗЫ И АДМИНА ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
        db.session.commit()

# --- МАРШРУТЫ ---
@app.route('/')
def index():
    services = Service.query.all()
    works = Work.query.all()
    return render_template('index.html', user=current_user, services=services, works=works)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '')
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Логин занят!', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
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
    
    msg = f"🆕 <b>Новый заказ!</b>\n\n"
    msg += f"👤 Клиент: {current_user.username}\n"
    msg += f"📦 Услуга: {service}\n"
    msg += f"📝 Описание: {description}\n"
    msg += f"🕒 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    send_telegram(msg)
    
    flash('Заказ отправлен!', 'success')
    return redirect(url_for('profile'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        
        contact = Contact(name=name, email=email, phone=phone, message=message)
        db.session.add(contact)
        db.session.commit()
        
        msg = f"📩 <b>Новое сообщение</b>\n\n"
        msg += f"👤 Имя: {name}\n"
        msg += f"📧 Email: {email}\n"
        msg += f"📞 Телефон: {phone}\n"
        msg += f"📝 Сообщение: {message}"
        send_telegram(msg)
        
        flash('Сообщение отправлено!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    services = Service.query.all()
    orders = Order.query.all()
    works = Work.query.all()
    contacts = Contact.query.all()
    return render_template('admin.html', services=services, orders=orders, works=works, contacts=contacts)

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

@app.route('/admin/edit_service/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_service(id):
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    service = Service.query.get(id)
    if request.method == 'POST':
        service.title = request.form['title']
        service.description = request.form['description']
        service.price = request.form['price']
        service.image_url = request.form['image_url']
        db.session.commit()
        flash('Услуга обновлена!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('edit_service.html', service=service)

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

@app.route('/admin/add_work', methods=['POST'])
@login_required
def add_work():
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    title = request.form['title']
    description = request.form['description']
    image_url = request.form['image_url']
    link = request.form['link']
    work = Work(title=title, description=description, image_url=image_url, link=link)
    db.session.add(work)
    db.session.commit()
    flash('Работа добавлена!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_work/<int:id>')
@login_required
def delete_work(id):
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    work = Work.query.get(id)
    db.session.delete(work)
    db.session.commit()
    flash('Работа удалена!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/order/<int:id>/status', methods=['POST'])
@login_required
def update_order_status(id):
    if not current_user.is_admin:
        return "Доступ запрещён", 403
    order = Order.query.get(id)
    order.status = request.form['status']
    db.session.commit()
    flash('Статус заказа обновлён!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            user.reset_token = token
            db.session.commit()
            flash('Ссылка для восстановления отправлена в Telegram', 'success')
            msg = f"🔐 <b>Восстановление пароля</b>\n\n"
            msg += f"👤 Логин: {user.username}\n"
            msg += f"🔑 Токен: {token}\n"
            msg += f"Перейдите по ссылке: https://my-first-web-app-hiif.onrender.com/reset-password/{token}"
            send_telegram(msg)
            return redirect(url_for('login'))
        flash('Пользователь не найден', 'danger')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('Неверная ссылка', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_password = request.form['password']
        user.password = new_password
        user.reset_token = None
        db.session.commit()
        flash('Пароль обновлён! Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)