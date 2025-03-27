from django.db import models
from canteens.models import Student, Menu

class Cart(models.Model):
    student_name = models.CharField(max_length=100, null=True, blank=True)  # Make optional
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_checked_out = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart for {self.student_name or self.student.name if self.student else 'Unknown'}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} in cart"

    @property
    def total_price(self):
        return self.quantity * self.menu_item.price