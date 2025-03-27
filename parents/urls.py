from django.urls import path
from parents import views

app_name = 'parents'

urlpatterns = [
    path('login/', views.login, name='parentlogin'),
    path('logout/', views.logout, name='parentlogout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recharge/<str:student_id>/', views.recharge_wallet, name='recharge_wallet'),
    path('confirm-recharge/<str:student_id>/', views.confirm_recharge, name='confirm_recharge'),
]