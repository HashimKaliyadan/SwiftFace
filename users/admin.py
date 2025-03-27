from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User
from canteens.models import Student
from django import forms

# Custom Admin Login Form
class AdminEmailLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs['placeholder'] = 'Enter your email'

# Custom User Creation Form for Admin
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('student_id', 'email', 'is_student', 'is_parent', 'is_canteen', 'is_staff', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].validators = []
        self.fields['password2'].validators = []
        self.fields['password1'].help_text = 'Enter an 8 character password .'
        self.fields['password2'].help_text = 'Confirm your password.'
        self.fields['email'].required = False

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        if password1 and len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        if password1 and not password1.isalnum():
            raise forms.ValidationError("Password can only contain letters and digits (no special characters).")

        return password2

# Inline Student Admin
class StudentInline(admin.StackedInline):
    model = Student
    fk_name = 'user'  # Specify the ForeignKey to use (links to User with is_student=True)
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fields = ('student_id', 'name', 'parent', 'parent_phone', 'face_image', 'balance')
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = User.objects.filter(is_parent=True)
            kwargs['required'] = False  # Make parent optional
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Custom User Admin
class UserAdmin(BaseUserAdmin):
    list_display = ('student_id', 'email', 'is_student', 'is_parent', 'is_canteen', 'is_staff', 'is_superuser', 'is_blocked')
    list_filter = ('is_student', 'is_parent', 'is_canteen', 'is_staff', 'is_superuser', 'is_blocked')
    search_fields = ('student_id', 'email')
    ordering = ('student_id',)
    inlines = [StudentInline]

    fieldsets = (
        (_('User Credentials'), {'fields': ('student_id', 'password')}),
        (_('Personal Information'), {'fields': ('email', 'phone_number', 'gender', 'dob')}),
        (_('Permissions'), {'fields': ('is_student', 'is_parent', 'is_canteen', 'is_staff', 'is_superuser', 'is_blocked')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (_('Create User'), {
            'classes': ('wide',),
            'fields': ('student_id', 'email', 'password1', 'password2', 'is_student', 'is_parent', 'is_canteen', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')
    login_form = AdminEmailLoginForm
    add_form = CustomUserCreationForm

# Register User with Custom Admin
admin.site.register(User, UserAdmin)