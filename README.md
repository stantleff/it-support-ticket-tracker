# IT Support Ticket Tracker

A recruiter-focused IT operations and support workflow platform built with Flask, Python, SQLite, SQLAlchemy, and a custom HTML/CSS interface.

## Project Overview

This application simulates the type of internal ticket management system used by IT support, technology operations, and business systems teams. The goal of the project is to demonstrate practical full-stack development, systems analysis, workflow design, and dashboard reporting in a way that connects directly to real entry-level technology roles.

Users can log in, create support tickets, assign technicians, update ticket status, add operational notes, monitor SLA status, filter ticket queues, and export reports.

## Demo Login

Use the following credentials when running the app locally:

```text
Username: demo
Password: password123
```

## Key Features

- Secure login and logout confirmation flow
- Operations dashboard with support workload metrics
- Ticket creation with category, priority, and technician assignment
- Ticket status updates for Open, In Progress, and Resolved workflows
- SLA tracking based on priority level
- Search and filtering by keyword, status, priority, and assigned technician
- Ticket detail pages with analyst notes/comments
- CSV export for operational reporting
- Demo data seeding for recruiter walkthroughs
- Professional responsive UI styling

## Screenshots

### Login Page
![Login Page](screenshots/login.png)

### Operations Dashboard
![Operations Dashboard](screenshots/dashboard.png)

### Dashboard Detail View
![Dashboard Detail View](screenshots/dashboard2.png)

### Ticket Queue
![Ticket Queue](screenshots/tickets.png)

### Create Ticket
![Create Ticket](screenshots/create-ticket.png)

### Ticket Detail
![Ticket Detail](screenshots/ticket-detail.png)

### Ticket Notes and Status Updates
![Ticket Notes and Status Updates](screenshots/ticket-detail2.png)

### Logout Confirmation
![Logout Confirmation](screenshots/logout.png)

## Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Werkzeug password hashing
- HTML
- CSS
- Jinja templates
- CSV reporting

## Local Setup

Clone the repository:

```bash
git clone https://github.com/stantleff/it-support-ticket-tracker.git
cd it-support-ticket-tracker
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:5000
```

Optional: after logging in, visit the route below to load demo tickets:

```text
http://127.0.0.1:5000/seed
```

## Recruiter Walkthrough

A suggested walkthrough for this project:

1. Log in using the demo account.
2. Review dashboard metrics such as open tickets, high-priority tickets, resolved tickets, and SLA overdue tickets.
3. Create a new ticket and assign a priority, category, and technician.
4. Open the ticket detail page and update the status.
5. Add an analyst note to show the operational history workflow.
6. Use filters on the ticket queue to search by status, priority, or technician.
7. Export the CSV report to demonstrate reporting functionality.
8. Log out using the confirmation page.

## Career Relevance

This project is designed to align with roles such as:

- Systems Analyst
- Business Systems Analyst
- IT Support Analyst
- Technology Operations Analyst
- Project Coordinator
- Junior Project Manager
- Operations Technology Associate

The project demonstrates more than basic coding. It shows the ability to design a business-facing workflow application with database persistence, user authentication, dashboard metrics, operational reporting, and a clean end-user experience.

## Future Enhancements

- Chart.js dashboard visualizations
- Dark mode toggle
- Role-based permissions
- Docker deployment
- Render cloud deployment
- Audit log history
- Advanced SLA reporting

## Author

Sawyer Tantleff
