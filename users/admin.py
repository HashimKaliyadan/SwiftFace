from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from users.models import User
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
        self.fields['password1'].help_text = 'Enter an 8 character password.'
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
    fields = ('id', 'student_id', 'name', 'parent', 'parent_phone', 'face_image', 'balance')  # Added 'id'
    readonly_fields = ('id',)  # Make 'id' read-only since it’s auto-generated
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = User.objects.filter(is_parent=True)
            kwargs['required'] = False  # Make parent optional
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Custom User Admin with Canteen Emphasis
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'is_canteen', 'is_student', 'is_parent', 'is_staff', 'is_superuser', 'is_blocked', 'date_joined')
    list_filter = ('is_canteen', 'is_student', 'is_parent', 'is_staff', 'is_superuser', 'is_blocked', 'is_active')
    search_fields = ('email',)  # Removed 'student_id' from search since it’s tied to Student
    ordering = ('-date_joined',)  # Order by most recent first
    inlines = [StudentInline]

    fieldsets = (
        (_('User Credentials'), {'fields': ('student_id', 'password')}),
        (_('Personal Information'), {'fields': ('email', 'phone_number', 'gender', 'dob')}),
        (_('Permissions'), {'fields': ('is_canteen', 'is_student', 'is_parent', 'is_staff', 'is_superuser', 'is_blocked', 'is_active')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (_('Create User'), {
            'classes': ('wide',),
            'fields': ('student_id', 'email', 'password1', 'password2', 'is_canteen', 'is_student', 'is_parent', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')
    login_form = AdminEmailLoginForm
    add_form = CustomUserCreationForm

    # Optionally restrict queryset to canteen staff for canteen-focused view
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Uncomment the line below to show only canteen staff by default
        # return qs.filter(is_canteen=True)
        return qs  # Keep all users visible, use filters instead

    def save_model(self, request, obj, form, change):
        """Ensure proper saving of user and related student profile if applicable"""
        super().save_model(request, obj, form, change)
        if obj.is_student and not hasattr(obj, 'student_profile'):
            Student.objects.create(user=obj, student_id=obj.student_id, name=f"Student {obj.student_id}")

# Register User with Custom Admin
admin.site.register(User, UserAdmin)