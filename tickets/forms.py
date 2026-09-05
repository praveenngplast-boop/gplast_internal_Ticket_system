from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from tickets.models import (
    Ticket, Unit, Department, AdminContact, AdminNotificationEmail, 
    EmployeeMaster, DepartmentCredential, ERPHolderMapping, UnitHead, TicketReply
)
from tickets.utils import validate_attachment


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['body', 'attachment']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Add an update or reply to this ticket...',
                'class': 'form-control',
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.txt',
            }),
        }

    def clean_body(self):
        body = self.cleaned_data.get('body', '').strip()
        if not body:
            raise ValidationError('Reply message cannot be empty.')
        return body

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            is_valid, message = validate_attachment(attachment)
            if not is_valid:
                raise ValidationError(message)
        return attachment


# ============================================================
# TICKET FORM
# ============================================================
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
        
        # ✅ Make mobile and email optional
        self.fields['mobile'].required = False
        self.fields['email'].required = False
        
        # ✅ Set help texts and placeholders for optional fields
        self.fields['mobile'].help_text = '10 digits only (optional)'
        self.fields['email'].help_text = 'Valid email format (optional)'
        self.fields['mobile'].widget.attrs.update({'placeholder': '10 digits (optional)'})
        self.fields['email'].widget.attrs.update({'placeholder': 'email@example.com (optional)'})
        
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
        mobile = self.cleaned_data.get('mobile')
        
        if mobile is None or mobile == '':
            return None
        
        mobile = mobile.strip()
        
        if mobile == '':
            return None
        
        if not mobile.isdigit():
            raise ValidationError("Mobile number must contain only digits.")
        
        if len(mobile) != 10:
            raise ValidationError("Mobile number must be exactly 10 digits.")
        
        return mobile

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if email is None or email == '':
            return None
        
        email = email.strip()
        
        if email == '':
            return None
        
        if '@' not in email or '.' not in email:
            raise ValidationError("Please enter a valid email address.")
        
        return email

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description) < 10:
            raise ValidationError("Detailed description must be at least 10 characters.")
        return description

    def clean_attachment_1(self):
        attachment = self.cleaned_data.get('attachment_1')
        if attachment:
            is_valid, message = validate_attachment(attachment)
            if not is_valid:
                raise ValidationError(message)
        return attachment

    def clean_attachment_2(self):
        attachment = self.cleaned_data.get('attachment_2')
        if attachment:
            is_valid, message = validate_attachment(attachment)
            if not is_valid:
                raise ValidationError(message)
        return attachment

    def clean_attachment_3(self):
        attachment = self.cleaned_data.get('attachment_3')
        if attachment:
            is_valid, message = validate_attachment(attachment)
            if not is_valid:
                raise ValidationError(message)
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


# ============================================================
# ADMIN TICKET FORM
# ============================================================
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


# ============================================================
# UNIT HEAD FORM - NEW
# ============================================================
class UnitHeadForm(forms.ModelForm):
    """
    Form for Admin to create/edit Unit Heads.
    Creates or updates Django User account automatically.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username (e.g., imd_head)'
        }),
        label='Username'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (min 8 characters)'
        }),
        required=False,
        label='Password'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        required=False,
        label='Confirm Password'
    )

    class Meta:
        model = UnitHead
        fields = ['unit', 'name', 'email', 'is_active']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        
        if self.is_edit:
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Leave blank to keep current password'
            self.fields['confirm_password'].required = False
            if self.instance and self.instance.pk and self.instance.user:
                self.initial['username'] = self.instance.user.username

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip().lower()
        
        if not username:
            raise ValidationError("Username is required.")
        
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        
        existing_user = User.objects.filter(username=username)
        if self.instance and self.instance.pk and self.instance.user:
            existing_user = existing_user.exclude(pk=self.instance.user.pk)
        
        if existing_user.exists():
            raise ValidationError(f"Username '{username}' is already taken. Please choose another.")
        
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if self.is_edit and not password:
            return password
        
        if not self.is_edit and not password:
            raise ValidationError("Password is required.")
        
        if password and len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        
        return password

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if self.is_edit and not password and not confirm_password:
            return confirm_password
        
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return confirm_password

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError("Email is required.")
        
        if '@' not in email or '.' not in email:
            raise ValidationError("Please enter a valid email address.")
        
        existing = UnitHead.objects.filter(email=email)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if self.instance and self.instance.pk and self.instance.user:
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.user.pk)
        else:
            existing_user = User.objects.filter(email=email)
        
        if existing.exists() or existing_user.exists():
            raise ValidationError("This email is already in use.")
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        unit = cleaned_data.get('unit')
        
        if not unit:
            raise ValidationError({"unit": "Please select a unit for this Unit Head."})
        
        existing = UnitHead.objects.filter(unit=unit)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError({
                "unit": f"This unit already has a head: {existing.first().name}"
            })
        
        return cleaned_data

    def save(self, commit=True):
        unit_head = super().save(commit=False)
        
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        email = self.cleaned_data.get('email')
        name = self.cleaned_data.get('name')
        
        user = None
        if self.instance and self.instance.pk:
            user = self.instance.user
        
        if user:
            user.username = username
            user.email = email
            user.first_name = name.split()[0] if name else ''
            user.last_name = ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
            
            if password:
                user.set_password(password)
            
            if commit:
                user.save()
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.first_name = name.split()[0] if name else ''
            user.last_name = ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
            user.is_staff = False
            user.is_superuser = False
            
            if commit:
                user.save()
        
        unit_head.user = user
        
        if commit:
            unit_head.save()
        
        return unit_head


# ============================================================
# ADMIN PASSWORD CHANGE FORM
# ============================================================
class AdminPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': f"Enter {field.label}"})


# ============================================================
# ADMIN SET USER PASSWORD FORM
# ============================================================
class AdminSetUserPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': f"Enter {field.label}"})


# ============================================================
# USER SELECTION FORM
# ============================================================
class UserSelectionForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False).order_by('username'), 
        label="Select Employee User", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# ============================================================
# ADMIN CONTACT FORM
# ============================================================
class AdminContactForm(forms.ModelForm):
    class Meta:
        model = AdminContact
        fields = ['admin_name', 'admin_phone', 'admin_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


# ============================================================
# UNIT FORM
# ============================================================
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


# ============================================================
# DEPARTMENT FORM - ✅ WITH DUPLICATE VALIDATION
# ============================================================
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['unit', 'name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif name == 'unit':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Department Name'})

    def clean(self):
        cleaned_data = super().clean()
        unit = cleaned_data.get('unit')
        name = cleaned_data.get('name')
        
        if unit and name:
            name = name.strip()
            
            existing = Department.objects.filter(
                unit=unit,
                name__iexact=name
            )
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'A department named "{name}" already exists in unit "{unit.code}". Please use a different name.'
                )
        
        return cleaned_data


# ============================================================
# ADMIN NOTIFICATION EMAIL FORM
# ============================================================
class AdminNotificationEmailForm(forms.ModelForm):
    class Meta:
        model = AdminNotificationEmail
        fields = ['email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Email Address'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})


# ============================================================
# DEPARTMENT CREDENTIAL FORM
# ============================================================
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
# CLOSE TICKET FORM - FIXED
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
        
        # ✅ Define sub-error choices for each main error type
        self.roadmap_sub_errors = [
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
        
        self.gpl_sub_errors = [
            ('', '-- Select Sub Error Type --'),
            ('User / Data Entry Error', 'User / Data Entry Error'),
            ('Process / Procedure Error', 'Process / Procedure Error'),
            ('Master Data Error', 'Master Data Error'),
            ('Other GPL Error', 'Other GPL Error'),
        ]
        
        # ✅ Set initial sub_error_type choices
        self.fields['sub_error_type'].choices = [('', '-- Select Sub Error Type --')]
        
        # ✅ If data is bound and main_error_type is set, update sub_error_type choices
        if self.data and self.data.get('main_error_type'):
            self._update_sub_error_choices(self.data.get('main_error_type'))
        
        # Add widget classes
        for name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs.update({'class': 'form-control'})
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
    
    def _update_sub_error_choices(self, main_error_type):
        """Update sub_error_type choices based on main_error_type"""
        if main_error_type == 'Roadmap Error':
            self.fields['sub_error_type'].choices = self.roadmap_sub_errors
            self.fields['sub_error_type'].required = True
        elif main_error_type == 'GPL Error':
            self.fields['sub_error_type'].choices = self.gpl_sub_errors
            self.fields['sub_error_type'].required = True
        else:
            self.fields['sub_error_type'].choices = [('', '-- Select Sub Error Type --')]
            self.fields['sub_error_type'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        main_error = cleaned_data.get('main_error_type')
        sub_error = cleaned_data.get('sub_error_type')
        closing_remarks = cleaned_data.get('closing_remarks')
        
        # ✅ Update sub_error_type choices based on main_error_type
        if main_error:
            self._update_sub_error_choices(main_error)
        
        # Validate sub_error_type when main_error_type is selected
        if main_error and main_error in ['Roadmap Error', 'GPL Error']:
            if not sub_error or sub_error == '':
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
        self.fields['employee'].queryset = EmployeeMaster.objects.filter(is_active=True).order_by('employee_id')
        
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