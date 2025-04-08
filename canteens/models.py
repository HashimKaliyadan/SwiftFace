from django.db import models
from users.models import User

class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='children',
        limit_choices_to={'is_parent': True},
        null=True,
        blank=True
    )
    parent_phone = models.CharField(max_length=15)
    face_image = models.ImageField(upload_to='students/', null=True, blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={'is_student': True}
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'canteen_students'
        verbose_name = 'student'
        verbose_name_plural = 'students'
        ordering = ['name']

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Category Image")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Menu(models.Model):
    name = models.CharField(max_length=100, verbose_name="Menu Name")
    image = models.ImageField(upload_to='menu/', blank=True, null=True, verbose_name="Menu Image")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    is_available = models.BooleanField(default=True, verbose_name="Available")

    class Meta:
        verbose_name_plural = "Menu Items"

    def __str__(self):
        return self.name

class Transaction(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    menu_item = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_canteen': True})

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.student.name} - {self.amount} ({self.timestamp})"
    
class Canteen(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_canteen': True})

    def __str__(self):
        return self.name    