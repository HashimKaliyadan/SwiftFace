from django import forms
from canteens.models import Student, Category, Menu, Transaction
from users.models import User
import random
import string

class StudentForm(forms.ModelForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'placeholder': 'Enter email'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}))

    class Meta:
        model = Student
        fields = ['student_id', 'name', 'parent', 'parent_phone', 'face_image', 'user', 'balance', 'email', 'password']
        widgets = {
            'student_id': forms.TextInput(attrs={'placeholder': 'Enter Student ID'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter Student Name'}),
            'parent': forms.Select(attrs={'placeholder': 'Select Parent'}),  # Dropdown for parent selection
            'parent_phone': forms.TextInput(attrs={'placeholder': 'Enter Parent Phone'}),
            'face_image': forms.FileInput(),
            'user': forms.Select(),  # Dropdown for selecting a User with is_student=True
            'balance': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit user choices to students only
        self.fields['user'].queryset = User.objects.filter(is_student=True)
        self.fields['user'].required = False  # Make user optional
        # Limit parent choices to parents only
        self.fields['parent'].queryset = User.objects.filter(is_parent=True)
        self.fields['parent'].required = False  # Make parent optional

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not user:
            if not email or not password:
                # Generate random email and password if none provided
                email = f"student_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}@example.com"
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                cleaned_data['email'] = email
                cleaned_data['password'] = password
            # If email and password are provided, they will be used as is
        return cleaned_data

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id']
        if Student.objects.filter(student_id=student_id).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A student with this ID already exists.")
        return student_id

    def clean_balance(self):
        balance = self.cleaned_data['balance']
        if balance < 0:
            raise forms.ValidationError("Balance cannot be negative.")
        return balance

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Category Name'}),
            'image': forms.FileInput(),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Category.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name', 'image', 'category', 'price', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Menu Item Name'}),
            'image': forms.FileInput(),
            'category': forms.Select(),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'is_available': forms.CheckboxInput(),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['student', 'amount', 'menu_item']
        widgets = {
            'student': forms.Select(),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'menu_item': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit menu_item choices to available items
        self.fields['menu_item'].queryset = Menu.objects.filter(is_available=True)
        self.fields['menu_item'].required = False  # Optional field

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        amount = cleaned_data.get('amount')
        if student and amount and student.balance < amount:
            raise forms.ValidationError("Student balance is insufficient for this transaction.")
        return cleaned_data