# tickets/views/auth_views.py

from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from tickets.models import AdminContact, UnitHead


@method_decorator(never_cache, name='dispatch')
class CustomLoginView(LoginView):
    """
    Custom login view with:
    - Contact information display
    - Role-based redirection (admin, unit head, employee)
    - Success/error messages
    - Authenticated user prevention
    """
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = AdminContact.objects.first()
        context['contact'] = contact
        return context
    
    def get_success_url(self):
        """Redirect to appropriate dashboard based on user role"""
        user = self.request.user
        
        # ✅ Check: Is Admin (is_staff)
        if user.is_staff:
            return '/custom-admin/dashboard/'
        
        # ✅ NEW: Check: Is Unit Head
        if UnitHead.objects.filter(user=user, is_active=True).exists():
            return '/unit-head/dashboard/'
        
        # Default: Employee
        return '/dashboard/'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        
        # Custom welcome message based on role
        if user.is_staff:
            welcome_msg = f"Welcome back, Admin {user.username}!"
        elif UnitHead.objects.filter(user=user, is_active=True).exists():
            unit_head = UnitHead.objects.filter(user=user, is_active=True).first()
            welcome_msg = f"Welcome back, {unit_head.name}! ({unit_head.unit.code} Unit Head)"
        else:
            welcome_msg = f"Welcome back, {user.username}!"
        
        messages.success(self.request, welcome_msg)
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user
            
            # ✅ Check: Is Admin
            if user.is_staff:
                return redirect('/custom-admin/dashboard/')
            
            # ✅ NEW: Check: Is Unit Head
            if UnitHead.objects.filter(user=user, is_active=True).exists():
                return redirect('/unit-head/dashboard/')
            
            # Default: Employee
            return redirect('/dashboard/')
        
        return super().dispatch(request, *args, **kwargs)


def role_redirect(request):
    """
    Redirect user to appropriate dashboard based on role.
    Priority: Admin > Unit Head > Employee
    """
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    user = request.user
    
    # ✅ Check: Is Admin (highest priority)
    if user.is_staff:
        return redirect('/custom-admin/dashboard/')
    
    # ✅ NEW: Check: Is Unit Head
    if UnitHead.objects.filter(user=user, is_active=True).exists():
        return redirect('/unit-head/dashboard/')
    
    # Default: Employee
    return redirect('/dashboard/')


def custom_logout(request):
    """Custom logout view with success message."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('/login/')