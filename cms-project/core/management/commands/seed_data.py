"""
Management command to seed the database with demo data.

Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Tenant, UserProfile, Complaint, AuditLog


class Command(BaseCommand):
    help = 'Seeds the database with demo tenants, users, and complaints'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with demo data...')
        
        tenant1 = Tenant.objects.create(
            name='Acme Corporation',
            slug='acme',
            is_active=True
        )
        self.stdout.write(f'  Created tenant: {tenant1.name}')
        
        tenant2 = Tenant.objects.create(
            name='TechStart Inc',
            slug='techstart',
            is_active=True
        )
        self.stdout.write(f'  Created tenant: {tenant2.name}')
        
        users_data = [
            {'username': 'admin', 'email': 'admin@acme.com', 'password': 'admin123', 
             'first_name': 'System', 'last_name': 'Admin', 'tenant': tenant1, 
             'role': UserProfile.ROLE_ADMIN, 'is_staff': True, 'is_superuser': True},
            {'username': 'manager1', 'email': 'manager@acme.com', 'password': 'manager123', 
             'first_name': 'John', 'last_name': 'Manager', 'tenant': tenant1, 
             'role': UserProfile.ROLE_MANAGER, 'is_staff': True},
            {'username': 'helpdesk1', 'email': 'helpdesk@acme.com', 'password': 'helpdesk123', 
             'first_name': 'Sarah', 'last_name': 'Helper', 'tenant': tenant1, 
             'role': UserProfile.ROLE_HELPDESK, 'is_staff': True},
            {'username': 'support1', 'email': 'support@acme.com', 'password': 'support123', 
             'first_name': 'Mike', 'last_name': 'Support', 'tenant': tenant1, 
             'role': UserProfile.ROLE_SUPPORT, 'is_staff': True},
            {'username': 'consumer1', 'email': 'consumer1@example.com', 'password': 'consumer123', 
             'first_name': 'Alice', 'last_name': 'Customer', 'tenant': tenant1, 
             'role': UserProfile.ROLE_CONSUMER},
            {'username': 'consumer2', 'email': 'consumer2@example.com', 'password': 'consumer123', 
             'first_name': 'Bob', 'last_name': 'Client', 'tenant': tenant1, 
             'role': UserProfile.ROLE_CONSUMER},
            {'username': 'ts_admin', 'email': 'admin@techstart.com', 'password': 'admin123', 
             'first_name': 'Tech', 'last_name': 'Admin', 'tenant': tenant2, 
             'role': UserProfile.ROLE_ADMIN, 'is_staff': True},
            {'username': 'ts_consumer', 'email': 'user@techstart.com', 'password': 'consumer123', 
             'first_name': 'Charlie', 'last_name': 'User', 'tenant': tenant2, 
             'role': UserProfile.ROLE_CONSUMER},
        ]
        
        created_users = {}
        for data in users_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_staff=data.get('is_staff', False),
                is_superuser=data.get('is_superuser', False)
            )
            UserProfile.objects.create(
                user=user,
                tenant=data['tenant'],
                role=data['role']
            )
            created_users[data['username']] = user
            self.stdout.write(f'  Created user: {user.username} ({data["role"]})')
        
        complaints_data = [
            {'title': 'Website not loading properly', 
             'description': 'The main website has been showing 500 errors intermittently since yesterday morning. I have tried clearing my cache and using different browsers but the issue persists.',
             'category': 'Technical', 'priority': Complaint.PRIORITY_HIGH,
             'status': Complaint.STATUS_IN_PROGRESS, 'submitted_by': 'consumer1',
             'assigned_to': 'support1', 'tenant': tenant1},
            {'title': 'Incorrect billing on last invoice', 
             'description': 'My last invoice shows a charge of $150 but I was only supposed to be charged $99 according to my subscription plan. Please review and correct.',
             'category': 'Billing', 'priority': Complaint.PRIORITY_MEDIUM,
             'status': Complaint.STATUS_OPEN, 'submitted_by': 'consumer1',
             'tenant': tenant1},
            {'title': 'Cannot access my account settings', 
             'description': 'When I try to access the account settings page, I get redirected back to the dashboard. This has been happening for the past 2 days.',
             'category': 'Technical', 'priority': Complaint.PRIORITY_MEDIUM,
             'status': Complaint.STATUS_RESOLVED, 'submitted_by': 'consumer2',
             'assigned_to': 'support1', 'tenant': tenant1,
             'resolution_notes': 'The issue was caused by a session cookie conflict. Cleared the session data and the user can now access settings normally.'},
            {'title': 'Request for feature enhancement', 
             'description': 'It would be great if you could add a dark mode option to the dashboard. Many users prefer working with darker interfaces.',
             'category': 'Feature Request', 'priority': Complaint.PRIORITY_LOW,
             'status': Complaint.STATUS_CLOSED, 'submitted_by': 'consumer2',
             'tenant': tenant1,
             'resolution_notes': 'Thank you for your suggestion. This has been added to our product roadmap.'},
            {'title': 'Mobile app crashes on startup', 
             'description': 'The mobile app keeps crashing immediately after I open it. I am using an iPhone 14 with iOS 17.',
             'category': 'Technical', 'priority': Complaint.PRIORITY_HIGH,
             'status': Complaint.STATUS_OPEN, 'submitted_by': 'ts_consumer',
             'tenant': tenant2},
        ]
        
        for data in complaints_data:
            complaint = Complaint.objects.create(
                tenant=data['tenant'],
                title=data['title'],
                description=data['description'],
                category=data['category'],
                priority=data['priority'],
                status=data['status'],
                submitted_by=created_users[data['submitted_by']],
                assigned_to=created_users.get(data.get('assigned_to')),
                resolution_notes=data.get('resolution_notes', '')
            )
            
            AuditLog.objects.create(
                tenant=data['tenant'],
                complaint=complaint,
                user=created_users[data['submitted_by']],
                action=AuditLog.ACTION_CREATED,
                details=f'Complaint created: {complaint.title}'
            )
            
            self.stdout.write(f'  Created complaint: {complaint.reference_number}')
        
        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('\nDemo Users (password in parentheses):')
        self.stdout.write('  Acme Corporation:')
        self.stdout.write('    admin / admin123 - System Administrator')
        self.stdout.write('    manager1 / manager123 - Manager')
        self.stdout.write('    helpdesk1 / helpdesk123 - Help Desk Agent')
        self.stdout.write('    support1 / support123 - Support Staff')
        self.stdout.write('    consumer1 / consumer123 - Consumer')
        self.stdout.write('    consumer2 / consumer123 - Consumer')
        self.stdout.write('  TechStart Inc:')
        self.stdout.write('    ts_admin / admin123 - System Administrator')
        self.stdout.write('    ts_consumer / consumer123 - Consumer')
