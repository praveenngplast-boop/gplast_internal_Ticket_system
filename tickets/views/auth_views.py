# tickets/views/auth_views.py
"""
Authentication views - Login, Logout, Role Redirect
"""
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache

from tickets.models import AdminContact


class CustomLoginView(LoginView):
    """
    Custom login view with:
    - Contact information display
    - Role-based redirection (admin vs employee)
    - Success/error messages
    - Authenticated user prevention
    """
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        """Add contact information to login page context"""
        context = super().get_context_data(**kwargs)
        contact = AdminContact.objects.first()
        context['contact'] = contact
        return context
    
    def get_success_url(self):
        """Redirect to appropriate dashboard based on user role"""
        if self.request.user.is_staff:
            return reverse_lazy('admin_dashboard')
        return reverse_lazy('employee_dashboard')
    
    def form_valid(self, form):
        """Add welcome message on successful login"""
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.username}!")
        return response
    
    def form_invalid(self, form):
        """Add error message on failed login"""
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)
    
    @never_cache
    def dispatch(self, request, *args, **kwargs):
        """
        Prevent authenticated users from accessing login page
        and redirect them to their dashboard
        """
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('admin_dashboard')
            return redirect('employee_dashboard')
        return super().dispatch(request, *args, **kwargs)


def role_redirect(request):
    """
    Redirect user to appropriate dashboard based on role.
    Used as a landing page after login.
    """
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('employee_dashboard')


def custom_logout(request):
    """
    Custom logout view with success message.
    Logs out the user and redirects to login page.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')