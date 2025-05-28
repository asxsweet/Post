
from flask import Flask, render_template, request, redirect
from models import db, Expense

app = Flask(__name__)

# 🔗 MySQL дерекқорына қосылу (PHPMyAdmin-де құрылған)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/budget_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 🔧 Кестені бір рет құру
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    expenses = Expense.query.all()
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['POST'])
def add():
    amount = request.form['amount']
    category = request.form['category']
    expense = Expense(amount=amount, category=category)
    db.session.add(expense)
    db.session.commit()
    return redirect('/')
