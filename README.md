# Multi-Tenant Complaint Management System PoC

A Proof of Concept (PoC) for a multi-tenant Complaint Management System built with Python and Django. This system validates the core architecture, data model, and complaint lifecycle for managing customer complaints across multiple organisations.

## Features

### User Roles
- **Consumer**: Submit complaints, view complaint status and history, confirm resolution
- **Help Desk Agent**: Log complaints on behalf of consumers, update status, assign to support staff
- **Support Staff**: Add resolution notes, update complaint status
- **Manager**: Full oversight of complaints and staff
- **System Administrator**: Full system access including Django Admin

### Core Functionality
- Multi-tenant architecture with complete data isolation per organisation
- Complaint lifecycle management: Open → In Progress → Resolved → Closed
- Role-based access control using Django's built-in permissions
- Audit logging for complaint creation, status changes, and assignments
- Server-rendered UI using Django templates

## Technology Stack
- **Backend**: Python 3.11 + Django 5.x
- **Database**: PostgreSQL (SQLite fallback for local development)
- **UI**: Django Templates with Bootstrap 5
- **Architecture**: Django MVT (Model-View-Template) pattern

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (optional, SQLite works for development)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd complaint-management-system
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install django psycopg2-binary python-dotenv gunicorn
```

4. Configure the database:
   - For PostgreSQL, set the `DATABASE_URL` environment variable
   - For SQLite (default), no configuration needed

5. Run migrations:
```bash
python manage.py migrate
```

6. (Optional) Seed demo data:
```bash
python manage.py seed_data
```

7. Start the development server:
```bash
python manage.py runserver
```

8. Access the application at `http://localhost:8000`

## Demo Users

After running `seed_data`, the following users are available:

### Acme Corporation
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | System Administrator |
| manager1 | manager123 | Manager |
| helpdesk1 | helpdesk123 | Help Desk Agent |
| support1 | support123 | Support Staff |
| consumer1 | consumer123 | Consumer |
| consumer2 | consumer123 | Consumer |

### TechStart Inc
| Username | Password | Role |
|----------|----------|------|
| ts_admin | admin123 | System Administrator |
| ts_consumer | consumer123 | Consumer |

## Project Structure

```
.
├── cms_project/           # Django project settings
│   ├── settings.py        # Configuration
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI entry point
├── core/                  # Main application
│   ├── models.py          # Data models (Tenant, UserProfile, Complaint, AuditLog)
│   ├── views.py           # View functions
│   ├── forms.py           # Django forms
│   ├── admin.py           # Admin configuration
│   ├── decorators.py      # Role-based access decorators
│   ├── middleware.py      # Tenant middleware
│   └── management/        # Custom management commands
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   └── core/              # App-specific templates
├── static/                # Static files (CSS, JS)
├── manage.py              # Django management script
└── main.py                # Application entry point
```

## Data Model

### Tenant
Represents an organisation in the multi-tenant system.

### UserProfile
Extends Django's User model with tenant association and role assignment.

### Complaint
Core entity with lifecycle states:
- **Open**: Initial state after submission
- **In Progress**: Being worked on by support staff
- **Resolved**: Resolution provided, awaiting consumer confirmation
- **Closed**: Consumer confirmed resolution

### AuditLog
Tracks key events: creation, status changes, assignments, resolution notes.

## API Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `/` | GET | Dashboard (role-based) |
| `/complaints/` | GET | List complaints |
| `/complaints/new/` | GET/POST | Create new complaint |
| `/complaints/<id>/` | GET | Complaint detail |
| `/complaints/<id>/status/` | POST | Update status |
| `/complaints/<id>/assign/` | POST | Assign to staff |
| `/complaints/<id>/resolution/` | POST | Add resolution notes |
| `/complaints/<id>/close/` | GET/POST | Consumer confirms resolution |
| `/admin/` | GET | Django Admin interface |

## Multi-Tenancy

- Each user belongs to exactly one tenant
- Complaints are isolated per tenant using foreign key relationships
- Query filtering ensures users never see data from other tenants
- Tenant context is attached to requests via middleware

## Success Criteria

This PoC demonstrates:
1. User authentication and login
2. Complaint creation and submission
3. Status updates through the complete lifecycle
4. Data isolation per tenant
5. Core architecture implementation as per design document

## License

This project is a Proof of Concept for academic purposes.
