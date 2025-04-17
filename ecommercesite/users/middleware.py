from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AdminAccessMiddleware:
    """Middleware to restrict access to the Django admin interface to staff members only."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.path.startswith('/admin/') and not request.user.is_superuser:
            return redirect('users:login')
        return self.get_response(request)