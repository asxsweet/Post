from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'өте_құпия_сөз_осында_болуы_керек'

# Дерекқор баптаулары
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# uploads папкасын жасау (егер жоқ болса)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Пост моделі
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100))  # Сурет жолы
    

# Қолданушы моделі
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Хештелген құпиясөз
    full_name = db.Column(db.String(150))  # толық аты
    email = db.Column(db.String(120), unique=True)
    profile_image = db.Column(db.String(100))  # профиль суреті жолы

# Негізгі бет
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        posts = Post.query.all()
        return render_template('index.html', posts=posts, user=user)
    return redirect(url_for('login'))


# Толық постты қарау
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)

# Пост қосу
@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_file = request.files.get('image')

        image_filename = None
        if image_file and image_file.filename != '':
            # Қауіпсіздік үшін secure_filename қолдануға болады (flask.helpers)
            from werkzeug.utils import secure_filename
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        new_post = Post(title=title, content=content, image=image_filename)
        db.session.add(new_post)
        db.session.commit()
        flash("Пост сәтті қосылды!", "success")
        return redirect(url_for('index'))

    return render_template('add_post.html')

# Постты өңдеу
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']

        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            from werkzeug.utils import secure_filename
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
            post.image = image_filename

        db.session.commit()
        flash("Пост сәтті өзгертілді!", "success")
        return redirect(url_for('index'))

    return render_template('change.html', post=post)

# Постты жою
@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Пост жойылды!", "success")
    return redirect(url_for('index'))

# Қолданушыны тіркеу
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Бұл логинмен қолданушы бар", "danger")
            return redirect(url_for('register'))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Тіркелу сәтті өтті! Енді кіріңіз.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Кіру
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Мысал: Пайдаланушыны базадан іздеу
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # ✅ user_id мәнін беру керек

            session['username'] = user.username
            session['fullname'] = user.full_name  # Мысалы: 'Әли Ахмет'
            session['profile_image'] = user.profile_image  # Мысалы: 'avatar.jpg'

            flash('Сәтті кірдіңіз!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Қате логин немесе құпиясөз', 'danger')

    return render_template('login.html')

# Шығу (logout)
@app.route('/logout')
def logout():
    session.clear()
    flash("Сіз сәтті шықтыңыз.", "info")
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Профильді көру үшін жүйеге кіріңіз", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Профильді өңдеу үшін жүйеге кіріңіз", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')

        image_file = request.files.get('profile_image')
        if image_file and image_file.filename != '':
            from werkzeug.utils import secure_filename
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            user.profile_image = filename
            session['profile_image'] = user.profile_image


        db.session.commit()
        flash("Профиль сәтті жаңартылды!", "success")
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)