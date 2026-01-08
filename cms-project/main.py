"""
Multi-Tenant Complaint Management System PoC

This is the main entry point for running the Django development server.
Standard Django commands can also be used:
  - python manage.py runserver 0.0.0.0:5000
  - python manage.py migrate
  - python manage.py createsuperuser
  - python manage.py seed_data
"""

import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:5000'])


if __name__ == '__main__':
    main()
