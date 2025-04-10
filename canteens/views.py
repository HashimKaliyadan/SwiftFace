from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.urls import reverse
from canteens.models import Student, Category, Menu, Transaction
from canteens.forms import StudentForm, CategoryForm, MenuForm, TransactionForm
from common.decorators import allow_canteen
import base64
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from users.models import User

# Dashboard with transaction overview
@login_required(login_url="/login/")
@allow_canteen
def index(request):
    total_students = Student.objects.count()
    total_categories = Category.objects.count()
    total_menu_items = Menu.objects.count()
    total_transactions = Transaction.objects.aggregate(total=Sum('amount'))['total'] or 0
    context = {
        "title": "Canteen Dashboard",
        "total_students": total_students,
        "total_categories": total_categories,
        "total_menu_items": total_menu_items,
        "total_transactions": total_transactions,
    }
    return render(request, "canteen/index.html", context)

# Login view
def login(request):
    if request.user.is_authenticated and request.user.is_canteen:
        return redirect('canteens:index')

    context = {"title": "Canteen | Login"}

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if email and password:
            user = authenticate(request, email=email, password=password)
            if user and user.is_canteen:
                auth_login(request, user)
                return redirect('canteens:index')
            else:
                messages.error(request, "Invalid email or password.")

    return render(request, "canteen/login.html", context)

@login_required
def logout(request):
    auth_logout(request)
    return redirect('students:home')

# Process payment (face recognition placeholder)
@login_required(login_url="/login/")
@allow_canteen
def process_payment(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            amount = form.cleaned_data['amount']
            menu_item = form.cleaned_data['menu_item']
            student.balance -= amount
            student.save()
            Transaction.objects.create(
                student=student,
                amount=amount,
                menu_item=menu_item,
                processed_by=request.user
            )
            messages.success(request, f"Payment of ${amount} processed for {student.name}.")
            return redirect('canteens:index')
        else:
            messages.error(request, "Payment failed. Check the details.")
    else:
        form = TransactionForm()
    context = {
        "title": "Canteen | Process Payment",
        "form": form,
    }
    return render(request, "canteen/process_payment.html", context)

# View all orders
@login_required(login_url="/login/")
@allow_canteen
def order_list(request):
    transactions = Transaction.objects.select_related('student', 'menu_item').all()
    context = {
        "title": "Canteen | All Orders",
        "transactions": transactions,
    }
    return render(request, "canteen/order_list.html", context)

@login_required(login_url="/login/")
@allow_canteen
def student_list(request):
    students = Student.objects.select_related('user').all()
    context = {"title": "Canteen | Students", "students": students}
    return render(request, "canteen/students.html", context)

# Add Student View
@login_required(login_url="/login/")
@allow_canteen
def add_student(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        
        # Handle the base64 image from the webcam
        face_image_data = post_data.get('face_image')
        if face_image_data and face_image_data.startswith('data:image'):
            format, imgstr = face_image_data.split(';base64,')
            ext = format.split('/')[-1]
            data = base64.b64decode(imgstr)
            file_io = BytesIO(data)
            image = Image.open(file_io)
            file_io.seek(0)
            image_file = InMemoryUploadedFile(
                file_io, None, f"face_image.{ext}", f"image/{ext}",
                len(data), None
            )
            request.FILES['face_image'] = image_file
        
        form = StudentForm(post_data, request.FILES or None)
        if form.is_valid():
            user = form.cleaned_data['user']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Create the student instance without saving to DB yet
            student = form.save(commit=False)

            if not user:
                # Create a new User if none is selected
                new_user = User.objects.create_user(
                    email=email,
                    password=password,
                    is_student=True
                )
                student.user = new_user  # Assign the new user directly to the student instance
            else:
                student.user = user  # Use the selected user

            # Save the student instance with the user set
            student.save()
            messages.success(request, f"Student {student.name} added successfully. Email: {email}")
            return redirect('canteens:canteen_students')
        else:
            messages.error(request, "Error adding student. Please check the form.")
    else:
        form = StudentForm()

    context = {"title": "Canteen | Add Student", "form": form}
    return render(request, "canteen/add_student.html", context)

# Edit Student View
@login_required(login_url="/login/")
@allow_canteen
def edit_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES or None, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student {student.name} updated successfully.")
            return redirect('canteens:canteen_students')
        else:
            messages.error(request, "Error updating student. Please check the form.")
    else:
        form = StudentForm(instance=student)
    context = {"title": "Canteen | Edit Student", "form": form, "student": student}
    return render(request, "canteen/edit_student.html", context)

# Delete Student View
@login_required(login_url="/login/")
@allow_canteen
def delete_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == "POST":
        student.delete()
        messages.success(request, f"Student {student.name} deleted successfully.")
        return redirect('canteens:canteen_students')
    context = {"title": "Canteen | Delete Student", "student": student}
    return render(request, "canteen/delete_student.html", context)

# Category management
@login_required(login_url="/login/")
@allow_canteen
def category_list(request):
    categories = Category.objects.all()
    context = {"title": "Canteen | Categories", "categories": categories}
    return render(request, "canteen/category_list.html", context)

@login_required(login_url="/login/")
@allow_canteen
def add_category(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, f"Category {category.name} added successfully.")
        return redirect('canteens:category_list')
    context = {"title": "Canteen | Add Category", "form": form}
    return render(request, "canteen/category_form.html", context)

@login_required(login_url="/login/")
@allow_canteen
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Category {category.name} updated successfully.")
        return redirect('canteens:category_list')
    context = {"title": "Canteen | Edit Category", "form": form}
    return render(request, "canteen/category_form.html", context)

@login_required(login_url="/login/")
@allow_canteen
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, f"Category {category.name} deleted successfully.")
        return redirect('canteens:category_list')
    context = {"title": "Canteen | Delete Category", "category": category}
    return render(request, "canteen/delete_category.html", context)

@login_required(login_url="/login/")
@allow_canteen
def menu_list(request):
    menus = Menu.objects.select_related('category').all()
    context = {"title": "Canteen | Menu", "menus": menus}
    return render(request, "canteen/menu_list.html", context)

@login_required(login_url="/login/")
@allow_canteen
def add_menu(request):
    form = MenuForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('canteens:menu_list')
    context = {"title": "Canteen | Add Menu Item", "form": form}
    return render(request, "canteen/menu_form.html", context)

@login_required(login_url="/login/")
@allow_canteen
def edit_menu(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    form = MenuForm(request.POST or None, request.FILES or None, instance=menu)
    if request.method == "POST" and form.is_valid():
        form.saveIt()
        return redirect('canteens:menu_list')
    context = {"title": "Canteen | Edit Menu Item", "form": form}
    return render(request, "canteen/menu_form.html", context)

@login_required(login_url="/login/")
@allow_canteen
def delete_menu(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    if request.method == "POST":
        menu.delete()
        return redirect('canteens:menu_list')
    context = {"title": "Canteen | Delete Menu Item", "menu": menu}
    return render(request, "canteen/delete_menu.html", context)

def register(request):
    if request.user.is_authenticated and request.user.is_canteen:
        return redirect('canteens:index')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "canteen/register.html", {"title": "Canteen | Register"})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "canteen/register.html", {"title": "Canteen | Register"})

        # Create new canteen staff user
        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                is_canteen=True  # Mark as canteen staff
            )
            messages.success(request, "Registration successful! Please log in.")
            return redirect('canteens:login')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")

    return render(request, "canteen/register.html", {"title": "Canteen | Register"})