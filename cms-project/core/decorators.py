"""
Custom decorators for role-based access control.
"""

from functools import wraps
from django.http import HttpResponseForbidden


def role_required(allowed_roles):
    """
    Decorator to restrict view access based on user role.
    
    Usage:
        @role_required(['helpdesk', 'manager', 'admin'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('Authentication required.')
            
            if not hasattr(request.user, 'profile'):
                return HttpResponseForbidden('User profile not configured.')
            
            user_role = request.user.profile.role
            if user_role not in allowed_roles:
                return HttpResponseForbidden(
                    'You do not have permission to perform this action.'
                )
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
