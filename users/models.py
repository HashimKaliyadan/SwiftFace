from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Others'),
)

class User(AbstractUser):
    username = None  # Remove the default username field
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)  # Added name field
    phone_number = models.CharField(
        max_length=15, null=True, blank=True, unique=True,
        error_messages={'unique': 'Mobile Number already exists'}
    )
    gender = models.CharField(max_length=1, null=True, blank=True, choices=GENDER_CHOICES)
    is_blocked = models.BooleanField(default=False)
    dob = models.DateTimeField(null=True, blank=True)
    is_canteen = models.BooleanField('Is canteen', default=False)
    is_parent = models.BooleanField('Is parent', default=False)
    is_student = models.BooleanField('Is student', default=False)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.name if self.name else (self.email if self.email else f"User {self.id}")

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'user_table'
        ordering = ['-id']