from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from canteens.models import Menu, Student, Transaction
from students.models import Cart, CartItem
from django.db import transaction
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from keras_facenet import FaceNet

# Load FaceNet model (no need for face_model.keras)
face_model = FaceNet()

def extract_face_embedding(image_data, model):
    # Convert base64 image data to embedding using FaceNet
    img = Image.open(BytesIO(image_data)).resize((160, 160))
    img_array = np.array(img)[np.newaxis, ...]  # Add batch dimension
    embedding = model.embeddings(img_array)
    return embedding[0]  # Return first embedding (single image)

def recognize_student(captured_image_data, current_student):
    from canteens.models import Student
    # Extract embedding for captured image
    captured_embedding = extract_face_embedding(captured_image_data, face_model)
    
    # Compare with all students' embeddings
    all_students = Student.objects.exclude(face_image__isnull=True)
    if not all_students:
        return False  # No students to compare with
    
    distances = {}
    for student in all_students:
        stored_img = Image.open(student.face_image.path).resize((160, 160))
        stored_array = np.array(stored_img)[np.newaxis, ...]
        stored_embedding = face_model.embeddings(stored_array)[0]
        distance = np.linalg.norm(captured_embedding - stored_embedding)
        distances[student.id] = distance
    
    # Find the closest match
    min_distance = min(distances.values())
    closest_student_id = min(distances, key=distances.get)
    
    # Threshold for FaceNet (0.8 is a good starting point; adjust as needed)
    threshold = 0.8
    if min_distance > threshold or closest_student_id != current_student.id:
        return False  # Invalid face detected
    return True  # Valid match

def home(request):
    menu_items = Menu.objects.filter(is_available=True)
    if request.method == "POST" and 'add_to_cart' in request.POST:
        menu_id = request.POST.get('menu_id')
        student_name = request.POST.get('student_name', 'Anonymous')
        menu_item = Menu.objects.get(id=menu_id)
        if request.user.is_authenticated and request.user.is_student:
            student = Student.objects.get(user=request.user)
            cart, _ = Cart.objects.get_or_create(student=student, is_checked_out=False)
        elif 'cart_id' in request.session:
            cart = Cart.objects.filter(id=request.session['cart_id'], is_checked_out=False).first()
            if not cart:
                cart = Cart.objects.create(student_name=student_name)
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create(student_name=student_name)
            request.session['cart_id'] = cart.id
        cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item)
        if not created:
            cart_item.quantity += 1
        cart_item.save()
        return redirect('students:home')
    context = {
        "title": "SwiftFace | Canteen",
        "menus": menu_items,
        "student": Student.objects.get(user=request.user) if request.user.is_authenticated and request.user.is_student else None,
    }
    return render(request, "students/home.html", context)

def cart(request):
    cart = None
    cart_items = []
    if request.user.is_authenticated and request.user.is_student:
        student = Student.objects.get(user=request.user)
        cart, _ = Cart.objects.get_or_create(student=student, is_checked_out=False)
    elif 'cart_id' in request.session:
        cart = Cart.objects.filter(id=request.session['cart_id'], is_checked_out=False).first()
    if cart:
        cart_items = cart.items.all()
    if request.method == "POST":
        if 'update_quantity' in request.POST:
            item_id = request.POST.get('item_id')
            new_quantity = int(request.POST.get('quantity'))
            cart_item = get_object_or_404(CartItem, id=item_id)
            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                cart_item.delete()
            return redirect('students:cart')
        elif 'remove_item' in request.POST:
            item_id = request.POST.get('item_id')
            cart_item = get_object_or_404(CartItem, id=item_id)
            cart_item.delete()
            return redirect('students:cart')
        elif 'checkout' in request.POST:
            if cart and request.user.is_authenticated and request.user.is_student:
                student = Student.objects.get(user=request.user)
                total = sum(item.total_price for item in cart_items)
                if student.balance >= total:
                    return redirect('students:face_recognition')
                else:
                    messages.error(request, "Insufficient balance.")
            return redirect('students:cart')
    context = {
        "title": "SwiftFace | Cart",
        "cart": cart,
        "cart_items": cart_items,
    }
    return render(request, "students/cart.html", context)

@login_required(login_url="/loginstudent/")
def face_recognition(request):
    if not request.user.is_student:
        messages.error(request, "Only students can access this page.")
        return redirect('students:home')
    student = Student.objects.get(user=request.user)
    cart = Cart.objects.filter(student=student, is_checked_out=False).first()
    if not cart:
        messages.error(request, "No items in cart.")
        return redirect('students:cart')
    total = sum(item.total_price for item in cart.items.all())
    if request.method == "POST":
        face_image_data = request.POST.get('face_image')
        if face_image_data and face_image_data.startswith('data:image'):
            format, imgstr = face_image_data.split(';base64,')
            data = base64.b64decode(imgstr)
            if recognize_student(data, student):
                if student.balance >= total:
                    with transaction.atomic():
                        student.balance -= total
                        student.save()
                        for item in cart.items.all():
                            Transaction.objects.create(
                                student=student,
                                amount=item.total_price,
                                menu_item=item.menu_item,
                                processed_by=None
                            )
                        cart.is_checked_out = True
                        cart.save()
                    if 'cart_id' in request.session:
                        del request.session['cart_id']
                    messages.success(request, "Payment completed successfully!")
                    return redirect('students:home')
                else:
                    messages.error(request, "Insufficient balance.")
            else:
                messages.error(request, "Invalid face detected")
        else:
            messages.error(request, "No face image captured")
        return redirect('students:face_recognition')
    context = {
        "title": "SwiftFace | Face Recognition",
        "student": student,
        "total": total,
    }
    return render(request, "students/face_recognition.html", context)

def student_login(request):
    if request.user.is_authenticated and request.user.is_student:
        return redirect('students:home')
    context = {"title": "Student | Login"}
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user and user.is_student:
                auth_login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect('students:home')
            else:
                messages.error(request, "Invalid credentials or not a student.")
        else:
            messages.error(request, "Please provide both email and password.")
    return render(request, "students/login.html", context)

def student_logout(request):
    auth_logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('students:home')

@login_required(login_url="/loginstudent/")
def wallet(request):
    if not request.user.is_student:
        messages.error(request, "Only students can view their wallet.")
        return redirect('students:home')
    student = Student.objects.get(user=request.user)
    context = {
        "title": "SwiftFace | Wallet",
        "student": student,
    }
    return render(request, "students/wallet.html", context)