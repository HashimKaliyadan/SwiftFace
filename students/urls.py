from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cart, name='cart'),
    path('face-recognition/', views.face_recognition, name='face_recognition'),
    path('wallet/', views.wallet, name="wallet"),
    path('loginstudent/', views.student_login, name="loginstudent"),
    path('logoutstudent/', views.student_logout, name="logoutstudent"),
]