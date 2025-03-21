from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, extract

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    month = request.args.get('month')
    if month:
        current_date = datetime.strptime(month, '%Y-%m')
    else:
        current_date = datetime.today()

    if request.method == 'POST':
        item = request.form['item']
        amount = int(request.form['amount'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        expense = Expense(item=item, amount=amount, date=date)
        db.session.add(expense)
        db.session.commit()
        return redirect(f'/?month={current_date.strftime("%Y-%m")}')

    start_month = current_date.replace(day=1)
    end_month = (start_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    expenses = Expense.query.filter(
        Expense.date >= start_month,
        Expense.date <= end_month
    ).order_by(Expense.date.asc()).all()

    weekly_expenses = db.session.query(
        extract('week', Expense.date).label('week'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.date >= start_month,
        Expense.date <= end_month
    ).group_by('week').all()

    month_total = sum(exp.amount for exp in expenses)

    prev_month = (start_month - timedelta(days=1)).strftime('%Y-%m')
    next_month = (end_month + timedelta(days=1)).strftime('%Y-%m')

    return render_template('index.html', expenses=expenses, weekly_expenses=weekly_expenses, month_total=month_total, current_date=current_date, prev_month=prev_month, next_month=next_month)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(request.referrer or '/')

@app.route('/calendar')
def calendar():
    month = request.args.get('month')
    if month:
        current_date = datetime.strptime(month, '%Y-%m')
    else:
        current_date = datetime.today()

    start_month = current_date.replace(day=1)
    end_month = (start_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    expenses = Expense.query.filter(
        Expense.date >= start_month,
        Expense.date <= end_month
    ).all()

    events = [{
        'title': f"{exp.item} ${exp.amount:,}",
        'start': exp.date.strftime('%Y-%m-%d')
    } for exp in expenses]

    # 傳入月份供前端日曆自動顯示
    return render_template('calendar.html', events=events, current_date=current_date)

if __name__ == '__main__':
    app.run(debug=True)
