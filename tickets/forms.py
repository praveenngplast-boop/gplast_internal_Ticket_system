from django import forms
from django.core.exceptions import ValidationError
from tickets.models import Ticket, Unit, Department, AdminContact, AdminNotificationEmail
from tickets.utils import validate_attachment

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'unit', 'department', 'employee_id', 'employee_name',
            'mobile', 'email', 'screen_number', 'subject',
            'description', 'priority', 'error_type', 'attachment'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit choices to active units only
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        # Limit choices to active departments
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        # Apply Bootstrap styling to all fields
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.RadioSelect)):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        # Restrict error type to employee-level choices only
        EMPLOYEE_ERROR_TYPE_CHOICES = [
            ('New', 'New'),
            ('Regular', 'Regular'),
            ('No Idea', 'No Idea'),
        ]
        self.fields['error_type'].choices = EMPLOYEE_ERROR_TYPE_CHOICES

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        # Only digits allowed, exactly 10, no spaces/dashes
        if not mobile.isdigit():
            raise ValidationError("Mobile number must contain digits only.")
        if len(mobile) != 10:
            raise ValidationError("Mobile number must be exactly 10 digits.")
        return mobile

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description) < 20:
            raise ValidationError("Detailed description must be at least 20 characters.")
        return description

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            validate_attachment(attachment)
        return attachment

    def clean(self):
        cleaned_data = super().clean()
        unit = cleaned_data.get('unit')
        department = cleaned_data.get('department')
        
        # Verify department belongs to the selected unit
        if unit and department:
            if department.unit != unit:
                raise ValidationError({"department": "Selected department does not belong to the selected unit."})
            if not department.is_active:
                raise ValidationError({"department": "Selected department is inactive."})
        return cleaned_data


class AdminTicketForm(TicketForm):
    # Overwrite Meta to add fields, widgets
    class Meta(TicketForm.Meta):
        fields = TicketForm.Meta.fields + ['created_by_role', 'admin_creation_reason']
        widgets = {
            **TicketForm.Meta.widgets,
            'created_by_role': forms.RadioSelect(choices=Ticket.CREATED_BY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling for admin fields
        self.fields['created_by_role'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['admin_creation_reason'].widget.attrs.update({'class': 'form-select'})
        
        # Set default role as Admin when created by admin (but user can toggle)
        self.initial['created_by_role'] = 'Admin'

    def clean(self):
        cleaned_data = super().clean()
        created_by_role = cleaned_data.get('created_by_role')
        admin_creation_reason = cleaned_data.get('admin_creation_reason')
        
        if created_by_role == 'Admin' and not admin_creation_reason:
            raise ValidationError({
                "admin_creation_reason": "Reason for Admin Creation is mandatory when Created By is 'Admin'."
            })
            
        # Clear reason if created by Employee
        if created_by_role == 'Employee':
            cleaned_data['admin_creation_reason'] = None
            
        return cleaned_data


# Settings Forms
class AdminContactForm(forms.ModelForm):
    class Meta:
        model = AdminContact
        fields = ['admin_name', 'admin_phone', 'admin_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['code', 'full_name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control', 'placeholder': f"Enter {name.replace('_', ' ')}"})

    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper()
        # Ensure only alphanumeric codes
        if not code.isalnum():
            raise ValidationError("Unit code must be alphanumeric.")
        return code


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['unit', 'name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.all()  # Allow selecting inactive for updates
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif name == 'unit':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Department Name'})


class AdminNotificationEmailForm(forms.ModelForm):
    class Meta:
        model = AdminNotificationEmail
        fields = ['email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Email Address'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
