from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

DB = SQLAlchemy(app)

class Ticket(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String(200), nullable=False)
    description = DB.Column(DB.Text, nullable=False)
    priority = DB.Column(DB.String(50), nullable=False)
    status = DB.Column(DB.String(50), default='Open')
    created_at = DB.Column(DB.DateTime, default=datetime.utcnow)

@app.route('/')
def dashboard():
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='Open').count()
    high_priority = Ticket.query.filter_by(priority='High').count()

    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    return render_template(
        'dashboard.html',
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        high_priority=high_priority,
        tickets=tickets
    )

@app.route('/tickets')
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/ticket/<int:ticket_id>')
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('ticket_detail.html', ticket=ticket)

@app.route('/create', methods=['GET', 'POST'])
def create_ticket():
    if request.method == 'POST':
        new_ticket = Ticket(
            title=request.form['title'],
            description=request.form['description'],
            priority=request.form['priority']
        )

        DB.session.add(new_ticket)
        DB.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('create_ticket.html')

if __name__ == '__main__':
    with app.app_context():
        DB.create_all()

    app.run(debug=True)
