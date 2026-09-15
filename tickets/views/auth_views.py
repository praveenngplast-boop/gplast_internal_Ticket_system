# tickets/views/auth_views.py

from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from tickets.models import AdminContact, UnitHead
from tickets.forms import CustomPasswordChangeForm

# ✅ NEW: import the sync helper
from tickets.views.utils import sync_department_credential_password


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


# ============================================================
# ✅ PASSWORD CHANGE VIEW
# Self-service password change for logged-in users.
# Enforces GPLAST policy: 4–14 chars, new ≠ old.
# Also mirrors the new plain password into the matching
# DepartmentCredential row so the admin credentials page
# reflects the change immediately.
# ============================================================
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'auth/password_change.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Keep the user logged in after the password change
        update_session_auth_hash(self.request, form.user)

        # ✅ NEW: Sync the new plain password into DepartmentCredential
        new_plain = form.cleaned_data.get('new_password1', '')
        if new_plain:
            try:
                updated = sync_department_credential_password(form.user, new_plain)
                if updated:
                    messages.info(
                        self.request,
                        "Your department credential has also been updated."
                    )
            except Exception as ex:
                # Never let a sync failure break the password change flow
                import logging
                logging.getLogger(__name__).error(
                    f"Credential sync failed for {form.user.username}: {ex}"
                )

        messages.success(
            self.request,
            "Your password has been changed successfully."
        )
        return response