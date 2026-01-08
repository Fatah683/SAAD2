"""
Views for the Multi-Tenant Complaint Management System.

Implements views for:
- Dashboard (role-based)
- Complaint CRUD operations
- Status updates and assignments
- Resolution confirmation
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseForbidden

from .models import Complaint, AuditLog, UserProfile
from .forms import ComplaintForm, ComplaintStatusForm, AssignmentForm, ResolutionForm
from .decorators import role_required


def get_tenant_complaints(user):
    """Get complaints filtered by user's tenant."""
    if hasattr(user, 'profile'):
        return Complaint.objects.filter(tenant=user.profile.tenant)
    return Complaint.objects.none()


def create_audit_log(complaint, user, action, details='', old_value='', new_value=''):
    """Helper function to create audit log entries."""
    AuditLog.objects.create(
        tenant=complaint.tenant,
        complaint=complaint,
        user=user,
        action=action,
        details=details,
        old_value=old_value,
        new_value=new_value
    )


@login_required
def dashboard(request):
    """
    Role-based dashboard view.
    Shows different information based on user role.
    """
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Your account is not properly configured. Please contact an administrator.')
        return redirect('login')
    
    profile = request.user.profile
    tenant = profile.tenant
    complaints = get_tenant_complaints(request.user)
    
    context = {
        'profile': profile,
        'tenant': tenant,
    }
    
    if profile.is_consumer():
        user_complaints = complaints.filter(submitted_by=request.user)
        context.update({
            'my_complaints': user_complaints[:5],
            'total_complaints': user_complaints.count(),
            'open_complaints': user_complaints.filter(status=Complaint.STATUS_OPEN).count(),
            'resolved_complaints': user_complaints.filter(status=Complaint.STATUS_RESOLVED).count(),
        })
    else:
        context.update({
            'total_complaints': complaints.count(),
            'open_complaints': complaints.filter(status=Complaint.STATUS_OPEN).count(),
            'in_progress': complaints.filter(status=Complaint.STATUS_IN_PROGRESS).count(),
            'resolved_complaints': complaints.filter(status=Complaint.STATUS_RESOLVED).count(),
            'closed_complaints': complaints.filter(status=Complaint.STATUS_CLOSED).count(),
            'unassigned': complaints.filter(assigned_to__isnull=True).exclude(status=Complaint.STATUS_CLOSED).count(),
            'recent_complaints': complaints[:10],
        })
        
        if profile.is_support():
            context['my_assigned'] = complaints.filter(assigned_to=request.user).exclude(
                status=Complaint.STATUS_CLOSED
            )[:5]
    
    return render(request, 'core/dashboard.html', context)


@login_required
def complaint_list(request):
    """
    List all complaints visible to the user.
    Consumers see only their complaints.
    Staff see all tenant complaints.
    """
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')
    
    profile = request.user.profile
    complaints = get_tenant_complaints(request.user)
    
    if profile.is_consumer():
        complaints = complaints.filter(submitted_by=request.user)
    
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)
    
    search = request.GET.get('search')
    if search:
        complaints = complaints.filter(
            Q(reference_number__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Complaint.STATUS_CHOICES,
        'priority_choices': Complaint.PRIORITY_CHOICES,
        'current_status': status_filter,
        'current_priority': priority_filter,
        'search': search or '',
    }
    
    return render(request, 'core/complaint_list.html', context)


@login_required
def complaint_detail(request, pk):
    """
    View complaint details.
    Includes complaint history (audit log).
    """
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')
    
    profile = request.user.profile
    complaint = get_object_or_404(Complaint, pk=pk, tenant=profile.tenant)
    
    if profile.is_consumer() and complaint.submitted_by != request.user:
        return HttpResponseForbidden('You do not have permission to view this complaint.')
    
    audit_logs = complaint.audit_logs.all()[:20]
    
    support_staff = UserProfile.objects.filter(
        tenant=profile.tenant,
        role__in=[UserProfile.ROLE_SUPPORT, UserProfile.ROLE_MANAGER]
    ).select_related('user')
    
    context = {
        'complaint': complaint,
        'audit_logs': audit_logs,
        'support_staff': support_staff,
        'can_assign': profile.is_helpdesk() or profile.is_manager() or profile.is_admin(),
        'can_update_status': profile.is_staff_member(),
        'can_add_resolution': profile.is_support() or profile.is_manager(),
        'can_close': profile.is_consumer() and complaint.submitted_by == request.user,
    }
    
    return render(request, 'core/complaint_detail.html', context)


@login_required
def complaint_create(request):
    """
    Create a new complaint.
    Consumers create for themselves.
    Help desk can create on behalf of consumers.
    """
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')
    
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, user=request.user)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = profile.tenant
            
            if profile.is_consumer():
                complaint.submitted_by = request.user
            else:
                complaint.logged_by = request.user
            
            complaint.save()
            
            create_audit_log(
                complaint=complaint,
                user=request.user,
                action=AuditLog.ACTION_CREATED,
                details=f'Complaint created: {complaint.title}'
            )
            
            messages.success(request, f'Complaint {complaint.reference_number} created successfully.')
            return redirect('complaint_detail', pk=complaint.pk)
    else:
        form = ComplaintForm(user=request.user)
    
    return render(request, 'core/complaint_form.html', {
        'form': form,
        'title': 'Submit New Complaint',
    })


@login_required
@role_required(['helpdesk', 'support', 'manager', 'admin'])
def complaint_update_status(request, pk):
    """Update complaint status (staff only)."""
    profile = request.user.profile
    complaint = get_object_or_404(Complaint, pk=pk, tenant=profile.tenant)
    
    if request.method == 'POST':
        form = ComplaintStatusForm(request.POST, instance=complaint)
        if form.is_valid():
            old_status = complaint.status
            new_status = form.cleaned_data['status']
            
            if complaint.can_update_status(new_status) or profile.is_admin():
                complaint.status = new_status
                complaint.save()
                
                create_audit_log(
                    complaint=complaint,
                    user=request.user,
                    action=AuditLog.ACTION_STATUS_CHANGE,
                    details=f'Status changed from {old_status} to {new_status}',
                    old_value=old_status,
                    new_value=new_status
                )
                
                messages.success(request, f'Status updated to {complaint.get_status_display()}.')
            else:
                messages.error(request, 'Invalid status transition.')
            
            return redirect('complaint_detail', pk=pk)
    
    return redirect('complaint_detail', pk=pk)


@login_required
@role_required(['helpdesk', 'manager', 'admin'])
def complaint_assign(request, pk):
    """Assign complaint to support staff."""
    profile = request.user.profile
    complaint = get_object_or_404(Complaint, pk=pk, tenant=profile.tenant)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, tenant=profile.tenant)
        if form.is_valid():
            old_assigned = complaint.assigned_to
            new_assigned = form.cleaned_data['assigned_to']
            
            complaint.assigned_to = new_assigned
            if complaint.status == Complaint.STATUS_OPEN:
                complaint.status = Complaint.STATUS_IN_PROGRESS
            complaint.save()
            
            old_name = old_assigned.username if old_assigned else 'Unassigned'
            new_name = new_assigned.username if new_assigned else 'Unassigned'
            
            create_audit_log(
                complaint=complaint,
                user=request.user,
                action=AuditLog.ACTION_ASSIGNED,
                details=f'Assigned to {new_name}',
                old_value=old_name,
                new_value=new_name
            )
            
            messages.success(request, f'Complaint assigned to {new_name}.')
            return redirect('complaint_detail', pk=pk)
    
    return redirect('complaint_detail', pk=pk)


@login_required
@role_required(['support', 'manager', 'admin'])
def complaint_add_resolution(request, pk):
    """Add resolution notes to a complaint."""
    profile = request.user.profile
    complaint = get_object_or_404(Complaint, pk=pk, tenant=profile.tenant)
    
    if request.method == 'POST':
        form = ResolutionForm(request.POST)
        if form.is_valid():
            complaint.resolution_notes = form.cleaned_data['resolution_notes']
            complaint.save()
            
            create_audit_log(
                complaint=complaint,
                user=request.user,
                action=AuditLog.ACTION_RESOLUTION_ADDED,
                details='Resolution notes updated'
            )
            
            messages.success(request, 'Resolution notes added.')
            return redirect('complaint_detail', pk=pk)
    
    return redirect('complaint_detail', pk=pk)


@login_required
def complaint_close(request, pk):
    """Consumer confirms resolution and closes complaint."""
    if not hasattr(request.user, 'profile'):
        return redirect('dashboard')
    
    profile = request.user.profile
    complaint = get_object_or_404(Complaint, pk=pk, tenant=profile.tenant)
    
    if complaint.submitted_by != request.user:
        return HttpResponseForbidden('Only the complaint owner can close it.')
    
    if complaint.status != Complaint.STATUS_RESOLVED:
        messages.error(request, 'Only resolved complaints can be closed.')
        return redirect('complaint_detail', pk=pk)
    
    if request.method == 'POST':
        complaint.status = Complaint.STATUS_CLOSED
        complaint.save()
        
        create_audit_log(
            complaint=complaint,
            user=request.user,
            action=AuditLog.ACTION_CLOSED,
            details='Consumer confirmed resolution and closed the complaint'
        )
        
        messages.success(request, 'Complaint closed successfully. Thank you for your feedback.')
        return redirect('complaint_detail', pk=pk)
    
    return render(request, 'core/complaint_close_confirm.html', {'complaint': complaint})
