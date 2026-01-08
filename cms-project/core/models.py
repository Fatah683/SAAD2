"""
Core models for the Multi-Tenant Complaint Management System.

This module defines the data models for:
- Tenant (organisation/multi-tenancy support)
- UserProfile (extends Django User with tenant and role)
- Complaint (core complaint entity with lifecycle states)
- AuditLog (tracking key events)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Tenant(models.Model):
    """
    Represents an organisation (tenant) in the multi-tenant system.
    All users and complaints belong to exactly one tenant.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """
    Extends the Django User model with tenant association and role.
    Each user belongs to exactly one tenant.
    """
    ROLE_CONSUMER = 'consumer'
    ROLE_HELPDESK = 'helpdesk'
    ROLE_SUPPORT = 'support'
    ROLE_MANAGER = 'manager'
    ROLE_ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (ROLE_CONSUMER, 'Consumer'),
        (ROLE_HELPDESK, 'Help Desk Agent'),
        (ROLE_SUPPORT, 'Support Staff'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_ADMIN, 'System Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CONSUMER)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) - {self.tenant.name}"

    def is_consumer(self):
        return self.role == self.ROLE_CONSUMER

    def is_helpdesk(self):
        return self.role == self.ROLE_HELPDESK

    def is_support(self):
        return self.role == self.ROLE_SUPPORT

    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_staff_member(self):
        """Returns True if user is helpdesk, support, manager, or admin."""
        return self.role in [self.ROLE_HELPDESK, self.ROLE_SUPPORT, self.ROLE_MANAGER, self.ROLE_ADMIN]


class Complaint(models.Model):
    """
    Core complaint entity with lifecycle states.
    
    Lifecycle: Open -> In Progress -> Resolved -> Closed
    """
    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='complaints')
    reference_number = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='submitted_complaints',
        help_text='The consumer who owns this complaint'
    )
    logged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='logged_complaints',
        help_text='Help desk agent who logged the complaint (if on behalf of consumer)'
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_complaints',
        help_text='Support staff assigned to resolve this complaint'
    )
    
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_number}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        
        if self.status == self.STATUS_RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        if self.status == self.STATUS_CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
            
        super().save(*args, **kwargs)

    def _generate_reference_number(self):
        """Generate a unique reference number for the complaint."""
        import uuid
        prefix = self.tenant.slug.upper()[:3] if self.tenant else 'CMP'
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{unique_id}"

    def can_update_status(self, new_status):
        """Check if status transition is valid."""
        valid_transitions = {
            self.STATUS_OPEN: [self.STATUS_IN_PROGRESS],
            self.STATUS_IN_PROGRESS: [self.STATUS_RESOLVED, self.STATUS_OPEN],
            self.STATUS_RESOLVED: [self.STATUS_CLOSED, self.STATUS_IN_PROGRESS],
            self.STATUS_CLOSED: [],
        }
        return new_status in valid_transitions.get(self.status, [])


class AuditLog(models.Model):
    """
    Audit logging for key events in the system.
    Tracks complaint creation, status updates, and assignments.
    """
    ACTION_CREATED = 'created'
    ACTION_STATUS_CHANGE = 'status_change'
    ACTION_ASSIGNED = 'assigned'
    ACTION_RESOLUTION_ADDED = 'resolution_added'
    ACTION_CLOSED = 'closed'
    
    ACTION_CHOICES = [
        (ACTION_CREATED, 'Complaint Created'),
        (ACTION_STATUS_CHANGE, 'Status Changed'),
        (ACTION_ASSIGNED, 'Complaint Assigned'),
        (ACTION_RESOLUTION_ADDED, 'Resolution Notes Added'),
        (ACTION_CLOSED, 'Complaint Closed'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='audit_logs')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint.reference_number} - {self.get_action_display()} by {self.user}"
