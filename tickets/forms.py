from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from tickets.models import Ticket, Unit, Department, AdminContact, AdminNotificationEmail, EmployeeMaster, DepartmentCredential, ERPHolderMapping
from tickets.utils import validate_attachment


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'unit', 'department', 'employee_id', 'employee_name',
            'mobile', 'email', 'screen_number', 'subject',
            'description', 'priority', 'error_type', 
            'attachment_1', 'attachment_2', 'attachment_3'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.RadioSelect)):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        # Only New and Repeated error types for employees
        EMPLOYEE_ERROR_TYPE_CHOICES = [
            ('New', 'New'),
            ('Repeated', 'Repeated'),
        ]
        self.fields['error_type'].choices = EMPLOYEE_ERROR_TYPE_CHOICES

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        if not mobile.isdigit():
            raise ValidationError("Mobile number must contain digits only.")
        if len(mobile) != 10:
            raise ValidationError("Mobile number must be exactly 10 digits.")
        return mobile

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description) < 10:
            raise ValidationError("Detailed description must be at least 10 characters.")
        return description

    def clean_attachment_1(self):
        attachment = self.cleaned_data.get('attachment_1')
        if attachment:
            validate_attachment(attachment)
        return attachment

    def clean_attachment_2(self):
        attachment = self.cleaned_data.get('attachment_2')
        if attachment:
            validate_attachment(attachment)
        return attachment

    def clean_attachment_3(self):
        attachment = self.cleaned_data.get('attachment_3')
        if attachment:
            validate_attachment(attachment)
        return attachment

    def clean(self):
        cleaned_data = super().clean()
        unit = cleaned_data.get('unit')
        department = cleaned_data.get('department')
        
        if unit and department:
            if department.unit != unit:
                raise ValidationError({"department": "Selected department does not belong to the selected unit."})
            if not department.is_active:
                raise ValidationError({"department": "Selected department is inactive."})
        return cleaned_data


class AdminTicketForm(TicketForm):
    class Meta(TicketForm.Meta):
        fields = TicketForm.Meta.fields + ['created_by_role', 'admin_creation_reason']
        widgets = {
            **TicketForm.Meta.widgets,
            'created_by_role': forms.RadioSelect(choices=Ticket.CREATED_BY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_by_role'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['admin_creation_reason'].widget.attrs.update({'class': 'form-select'})
        self.initial['created_by_role'] = 'Admin'

        # Also update error_type for AdminTicketForm to only New and Repeated
        EMPLOYEE_ERROR_TYPE_CHOICES = [
            ('New', 'New'),
            ('Repeated', 'Repeated'),
        ]
        self.fields['error_type'].choices = EMPLOYEE_ERROR_TYPE_CHOICES

    def clean(self):
        cleaned_data = super().clean()
        created_by_role = cleaned_data.get('created_by_role')
        admin_creation_reason = cleaned_data.get('admin_creation_reason')
        
        if created_by_role == 'Admin' and not admin_creation_reason:
            raise ValidationError({
                "admin_creation_reason": "Reason for Admin Creation is mandatory when Created By is 'Admin'."
            })
            
        if created_by_role == 'Employee':
            cleaned_data['admin_creation_reason'] = None
            
        return cleaned_data


class AdminPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': f"Enter {field.label}"})


class AdminSetUserPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': f"Enter {field.label}"})


class UserSelectionForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False).order_by('username'), 
        label="Select Employee User", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )


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
        if not code.isalnum():
            raise ValidationError("Unit code must be alphanumeric.")
        return code


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['unit', 'name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.all()
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


class DepartmentCredentialForm(forms.ModelForm):
    class Meta:
        model = DepartmentCredential
        fields = ['unit', 'department', 'username', 'password', 'is_active']
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}, render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif name in ['unit', 'department']:
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        unit = cleaned_data.get('unit')
        department = cleaned_data.get('department')
        
        if unit and department:
            if department.unit != unit:
                raise ValidationError({
                    "department": "Selected department does not belong to the selected unit."
                })
        return cleaned_data


# ============================================================
# CLOSE TICKET FORM - Used for admin closing tickets
# ============================================================
class CloseTicketForm(forms.Form):
    """
    Form for closing a ticket with new error type structure.
    Used in the admin ticket detail view.
    """
    main_error_type = forms.ChoiceField(
        choices=[
            ('', '-- Select Error Type --'),
            ('Roadmap Error', 'Roadmap Error'),
            ('GPL Error', 'GPL Error'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'mainErrorType'})
    )
    
    sub_error_type = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'subErrorType'})
    )
    
    closing_remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter resolution details...',
            'id': 'closingRemarks'
        }),
        required=True,
        label='Closing Remarks'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set sub_error_type choices based on main_error_type if provided
        main_error = self.data.get('main_error_type') if self.data else None
        
        if main_error == 'Roadmap Error':
            self.fields['sub_error_type'].choices = [
                ('', '-- Select Sub Error Type --'),
                ('Database Error', 'Database Error'),
                ('Logic / Functional Error', 'Logic / Functional Error'),
                ('Application Error', 'Application Error'),
                ('Calculation Error', 'Calculation Error'),
                ('Report / Print Error', 'Report / Print Error'),
                ('Workflow / Approval Error', 'Workflow / Approval Error'),
                ('Integration / API Error', 'Integration / API Error'),
                ('Barcode Error', 'Barcode Error'),
                ('Performance Error', 'Performance Error'),
                ('Access / Permission Error', 'Access / Permission Error'),
                ('Master Data / Configuration Error', 'Master Data / Configuration Error'),
                ('Other ERP Error', 'Other ERP Error'),
            ]
            self.fields['sub_error_type'].required = True
        elif main_error == 'GPL Error':
            self.fields['sub_error_type'].choices = [
                ('', '-- Select Sub Error Type --'),
                ('User / Data Entry Error', 'User / Data Entry Error'),
                ('Process / Procedure Error', 'Process / Procedure Error'),
                ('Master Data Error', 'Master Data Error'),
                ('Other GPL Error', 'Other GPL Error'),
            ]
            self.fields['sub_error_type'].required = True
        else:
            self.fields['sub_error_type'].choices = [('', '-- Select Sub Error Type --')]
            self.fields['sub_error_type'].required = False
        
        # Add widget classes
        for name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs.update({'class': 'form-control'})
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
    
    def clean(self):
        cleaned_data = super().clean()
        main_error = cleaned_data.get('main_error_type')
        sub_error = cleaned_data.get('sub_error_type')
        closing_remarks = cleaned_data.get('closing_remarks')
        
        # Validate sub_error_type when main_error_type is selected
        if main_error and main_error in ['Roadmap Error', 'GPL Error']:
            if not sub_error:
                raise ValidationError({
                    'sub_error_type': 'Please select a sub-error type for the selected error category.'
                })
        
        # Validate closing remarks
        if closing_remarks and len(closing_remarks.strip()) < 5:
            raise ValidationError({
                'closing_remarks': 'Closing remarks must be at least 5 characters.'
            })
        
        return cleaned_data


# ============================================================
# ERP USER ID MAPPING FORM
# ============================================================
class ERPHolderMappingForm(forms.ModelForm):
    """
    Form for mapping ERP User IDs to Employee IDs
    """
    class Meta:
        model = ERPHolderMapping
        fields = ['erp_user_id', 'employee']
        widgets = {
            'erp_user_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ERP User ID (e.g., 0001)'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active employees
        self.fields['employee'].queryset = EmployeeMaster.objects.filter(is_active=True).order_by('employee_id')
        
        # Add help text
        self.fields['erp_user_id'].help_text = "Enter the ERP User ID (e.g., 0001, 0002)"
        self.fields['employee'].help_text = "Select the employee to map to this ERP User ID"

    def clean_erp_user_id(self):
        erp_user_id = self.cleaned_data.get('erp_user_id', '').strip()
        if not erp_user_id:
            raise ValidationError("ERP User ID is required")
        return erp_user_id

    def clean(self):
        cleaned_data = super().clean()
        erp_user_id = cleaned_data.get('erp_user_id')
        employee = cleaned_data.get('employee')
        
        if erp_user_id and employee:
            # Check if mapping already exists (for update)
            instance = self.instance
            exists = ERPHolderMapping.objects.filter(
                erp_user_id=erp_user_id,
                employee=employee
            )
            if instance and instance.pk:
                exists = exists.exclude(pk=instance.pk)
            
            if exists.exists():
                raise ValidationError(
                    f'Mapping already exists: ERP {erp_user_id} → {employee.employee_id} ({employee.employee_name})'
                )
        
        return cleaned_data