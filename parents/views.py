from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from canteens.models import Student, Transaction, Menu 
from students.models import Cart, CartItem
from decimal import Decimal 

def login(request):
    if request.user.is_authenticated and request.user.is_parent:
        return redirect('parents:dashboard')
    context = {"title": "Parent | Login"}
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user and user.is_parent:
                auth_login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect('parents:dashboard')
            else:
                messages.error(request, "Invalid credentials or not a parent.")
        else:
            messages.error(request, "Please provide both email and password.")
    return render(request, "parent/login.html", context)

@login_required(login_url="/parents/login/")
def logout(request):
    auth_logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('students:home')

@login_required(login_url="/parents/login/")
def dashboard(request):
    if not request.user.is_parent:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('students:home')

    students = Student.objects.filter(parent=request.user)
    orders = Transaction.objects.filter(student__in=students).select_related('menu_item')
    menu_items = Menu.objects.filter(is_available=True)

    if request.method == "POST":
        student_id = request.POST.get('student_id')
        menu_item_id = request.POST.get('menu_item_id')
        try:
            student = Student.objects.get(student_id=student_id, parent=request.user)
            menu_item = Menu.objects.get(id=menu_item_id, is_available=True)
            
            if student.balance >= menu_item.price:
                with transaction.atomic():
                    # Deduct balance
                    student.balance -= menu_item.price
                    student.save()

                    # Add to student's cart
                    cart, created = Cart.objects.get_or_create(
                        student=student,
                        is_checked_out=False,
                        defaults={'student_name': student.name}  # Set student_name if needed
                    )
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=cart,
                        menu_item=menu_item,
                        defaults={'quantity': 1}
                    )
                    if not item_created:  # If item exists, increment quantity
                        cart_item.quantity += 1
                        cart_item.save()  # total_price is calculated dynamically via @property

                    # Optional: Create a transaction record
                    Transaction.objects.create(
                        student=student,
                        amount=menu_item.price,
                        menu_item=menu_item,
                        processed_by=None
                    )

                messages.success(request, f"Pre-order for {menu_item.name} placed successfully for {student.name}!")
            else:
                messages.error(request, f"Insufficient balance for {student.name} to pre-order {menu_item.name}.")
        except Student.DoesNotExist:
            messages.error(request, "Selected student not found.")
        except Menu.DoesNotExist:
            messages.error(request, "Selected menu item not found or unavailable.")
        return redirect('parents:dashboard')

    context = {
        "title": "Parent | Dashboard",
        "students": students,
        "orders": orders,
        "menu_items": menu_items,
        "user": request.user,
    }
    return render(request, "parent/dashboard.html", context)

@login_required(login_url="/parents/login/")
def recharge_wallet(request, student_id):
    student = Student.objects.get(student_id=student_id, parent=request.user)
    if request.method == "POST":
        amount = request.POST.get('amount', 0)
        try:
            # Convert the amount to Decimal
            amount = Decimal(amount)
            if amount > 0:
                # Redirect to a confirmation page
                return render(request, "parent/confirm_recharge.html", {
                    "student": student,
                    "amount": amount,
                })
            else:
                messages.error(request, "Please enter a valid amount.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount. Please enter a valid number.")
    context = {"title": "Recharge Wallet", "student": student}
    return render(request, "parent/recharge.html", context)

@login_required(login_url="/parents/login/")
def confirm_recharge(request, student_id):
    if request.method == "POST":
        student = Student.objects.get(student_id=student_id, parent=request.user)
        amount = request.POST.get('amount', 0)
        try:
            # Convert the amount to Decimal
            amount = Decimal(amount)
            if amount > 0:
                student.balance += amount  # Now both are Decimal objects
                student.save()
                messages.success(request, f"Wallet recharged with ${amount} for {student.name}.")
                return redirect('parents:dashboard')
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount. Please enter a valid number.")
    return redirect('parents:recharge_wallet', student_id=student_id)
