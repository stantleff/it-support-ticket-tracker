import csv
import io
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key-before-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tickets.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

DB = SQLAlchemy(app)


class User(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    username = DB.Column(DB.String(80), unique=True, nullable=False)
    password_hash = DB.Column(DB.String(255), nullable=False)
    role = DB.Column(DB.String(50), default='Analyst')


class Ticket(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String(200), nullable=False)
    description = DB.Column(DB.Text, nullable=False)
    category = DB.Column(DB.String(80), nullable=False, default='General Support')
    priority = DB.Column(DB.String(50), nullable=False)
    status = DB.Column(DB.String(50), default='Open')
    assigned_to = DB.Column(DB.String(100), default='Unassigned')
    created_at = DB.Column(DB.DateTime, default=datetime.utcnow)
    updated_at = DB.Column(DB.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = DB.Column(DB.DateTime, nullable=True)

    notes = DB.relationship('TicketNote', backref='ticket', lazy=True, cascade='all, delete-orphan')

    @property
    def sla_due_at(self):
        hours = {'High': 4, 'Medium': 24, 'Low': 72}.get(self.priority, 24)
        return self.created_at + timedelta(hours=hours)

    @property
    def sla_status(self):
        if self.status == 'Resolved':
            return 'Met' if self.resolved_at and self.resolved_at <= self.sla_due_at else 'Missed'
        return 'Overdue' if datetime.utcnow() > self.sla_due_at else 'On Track'


class TicketNote(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    ticket_id = DB.Column(DB.Integer, DB.ForeignKey('ticket.id'), nullable=False)
    author = DB.Column(DB.String(100), default='Support Analyst')
    note = DB.Column(DB.Text, nullable=False)
    created_at = DB.Column(DB.DateTime, default=datetime.utcnow)


def migrate_database():
    inspector = inspect(DB.engine)
    if 'ticket' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('ticket')}
    migrations = {
        'category': "ALTER TABLE ticket ADD COLUMN category VARCHAR(80) NOT NULL DEFAULT 'General Support'",
        'assigned_to': "ALTER TABLE ticket ADD COLUMN assigned_to VARCHAR(100) DEFAULT 'Unassigned'",
        'updated_at': 'ALTER TABLE ticket ADD COLUMN updated_at DATETIME',
        'resolved_at': 'ALTER TABLE ticket ADD COLUMN resolved_at DATETIME',
    }

    for column_name, statement in migrations.items():
        if column_name not in existing_columns:
            DB.session.execute(text(statement))

    DB.session.commit()


def initialize_database():
    with app.app_context():
        DB.create_all()
        migrate_database()
        seed_demo_user()


def login_required(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return route(*args, **kwargs)
    return wrapper


def current_user():
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])


def seed_demo_user():
    if not User.query.filter_by(username='demo').first():
        user = User(
            username='demo',
            password_hash=generate_password_hash('password123'),
            role='Support Analyst'
        )
        DB.session.add(user)
        DB.session.commit()


def count_by_field(tickets, field_name):
    counts = {}
    for ticket in tickets:
        value = getattr(ticket, field_name) or 'Unassigned'
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_chart_payload(labels, counts):
    return {
        'labels': labels,
        'data': [counts.get(label, 0) for label in labels]
    }


@app.context_processor
def inject_user():
    return {'current_user': current_user()}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()

        if user and check_password_hash(user.password_hash, request.form.get('password', '')):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.')

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'POST':
        session.clear()
        flash('You have been logged out successfully.')
        return redirect(url_for('login'))
    return render_template('logout.html')


@app.route('/')
@login_required
def dashboard():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='Open').count()
    in_progress = Ticket.query.filter_by(status='In Progress').count()
    resolved = Ticket.query.filter_by(status='Resolved').count()
    high_priority = Ticket.query.filter_by(priority='High').count()
    overdue = sum(1 for ticket in tickets if ticket.sla_status == 'Overdue')

    priority_counts = {
        'High': Ticket.query.filter_by(priority='High').count(),
        'Medium': Ticket.query.filter_by(priority='Medium').count(),
        'Low': Ticket.query.filter_by(priority='Low').count(),
    }

    status_counts = {
        'Open': open_tickets,
        'In Progress': in_progress,
        'Resolved': resolved,
    }

    sla_labels = ['On Track', 'Overdue', 'Met', 'Missed']
    sla_counts = {label: 0 for label in sla_labels}
    for ticket in tickets:
        sla_counts[ticket.sla_status] = sla_counts.get(ticket.sla_status, 0) + 1

    technician_counts = count_by_field(tickets, 'assigned_to')
    top_technicians = sorted(technician_counts.items(), key=lambda item: item[1], reverse=True)[:6]
    technician_chart = {
        'labels': [name for name, _ in top_technicians] or ['No Tickets'],
        'data': [count for _, count in top_technicians] or [0]
    }

    chart_data = {
        'priority': build_chart_payload(['High', 'Medium', 'Low'], priority_counts),
        'status': build_chart_payload(['Open', 'In Progress', 'Resolved'], status_counts),
        'sla': build_chart_payload(sla_labels, sla_counts),
        'technicians': technician_chart,
    }

    return render_template(
        'dashboard.html',
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress=in_progress,
        resolved=resolved,
        high_priority=high_priority,
        overdue=overdue,
        tickets=tickets[:8],
        priority_counts=priority_counts,
        status_counts=status_counts,
        chart_data=chart_data
    )


@app.route('/tickets')
@login_required
def tickets():
    query = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    assigned_to = request.args.get('assigned_to', '')

    ticket_query = Ticket.query

    if query:
        ticket_query = ticket_query.filter(
            (Ticket.title.ilike(f'%{query}%')) |
            (Ticket.description.ilike(f'%{query}%'))
        )

    if status:
        ticket_query = ticket_query.filter_by(status=status)

    if priority:
        ticket_query = ticket_query.filter_by(priority=priority)

    if assigned_to:
        ticket_query = ticket_query.filter(Ticket.assigned_to.ilike(f'%{assigned_to}%'))

    tickets = ticket_query.order_by(Ticket.created_at.desc()).all()

    return render_template(
        'tickets.html',
        tickets=tickets,
        query=query,
        status=status,
        priority=priority,
        assigned_to=assigned_to
    )


@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if request.method == 'POST':
        ticket.status = request.form.get('status', ticket.status)
        ticket.priority = request.form.get('priority', ticket.priority)
        ticket.assigned_to = request.form.get('assigned_to', 'Unassigned')

        if ticket.status == 'Resolved' and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        elif ticket.status != 'Resolved':
            ticket.resolved_at = None

        DB.session.commit()
        flash('Ticket updated successfully.')

        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    return render_template('ticket_detail.html', ticket=ticket)


@app.route('/ticket/<int:ticket_id>/note', methods=['POST'])
@login_required
def add_note(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    note_text = request.form.get('note', '').strip()

    if note_text:
        note = TicketNote(
            ticket_id=ticket.id,
            author=session.get('username', 'Support Analyst'),
            note=note_text
        )

        DB.session.add(note)
        DB.session.commit()
        flash('Note added.')

    return redirect(url_for('ticket_detail', ticket_id=ticket.id))


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        new_ticket = Ticket(
            title=request.form.get('title', 'Untitled Ticket'),
            description=request.form.get('description', ''),
            category=request.form.get('category', 'General Support'),
            priority=request.form.get('priority', 'Medium'),
            assigned_to=request.form.get('assigned_to', 'Unassigned')
        )

        DB.session.add(new_ticket)
        DB.session.commit()

        flash('Ticket created successfully.')
        return redirect(url_for('dashboard'))

    return render_template('create_ticket.html')


@app.route('/reports/export')
@login_required
def export_report():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'ID',
        'Title',
        'Category',
        'Priority',
        'Status',
        'Assigned To',
        'Created At',
        'SLA Due At',
        'SLA Status'
    ])

    for ticket in tickets:
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.category,
            ticket.priority,
            ticket.status,
            ticket.assigned_to,
            ticket.created_at,
            ticket.sla_due_at,
            ticket.sla_status,
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=it_ticket_report.csv'}
    )


@app.route('/seed')
@login_required
def seed_data():
    if Ticket.query.count() == 0:
        demo_tickets = [
            Ticket(title='Employee cannot access VPN', description='User receives authentication error when connecting remotely.', category='Network', priority='High', assigned_to='Jordan Lee'),
            Ticket(title='Laptop running slow after update', description='Device performance dropped after recent software updates.', category='Hardware', priority='Medium', assigned_to='Morgan Smith'),
            Ticket(title='New hire email setup', description='Create mailbox and assign standard onboarding permissions.', category='Account Access', priority='Low', assigned_to='Taylor Brooks'),
            Ticket(title='Printer offline in finance office', description='Shared office printer is unavailable to the finance team.', category='Hardware', priority='Medium', assigned_to='Unassigned'),
        ]

        DB.session.add_all(demo_tickets)
        DB.session.commit()
        flash('Demo tickets added.')
    else:
        flash('Demo data already exists.')

    return redirect(url_for('dashboard'))


initialize_database()

if __name__ == '__main__':
    app.run(debug=True)
