"""
Middleware for tenant-based request handling.
"""


class TenantMiddleware:
    """
    Middleware to attach tenant information to the request object.
    This allows easy access to the current tenant throughout the request lifecycle.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.tenant = None
        
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            request.tenant = request.user.profile.tenant
        
        response = self.get_response(request)
        return response
