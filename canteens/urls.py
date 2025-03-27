from django.urls import path
from canteens import views

app_name = 'canteens'

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('process-payment/', views.process_payment, name="process_payment"),
    path('orders/', views.order_list, name="order_list"),  # New URL for orders
    path('students/', views.student_list, name="canteen_students"),
    path('students/add/', views.add_student, name="add_student"),
    path('students/edit/<str:student_id>/', views.edit_student, name="edit_student"),
    path('students/delete/<str:student_id>/', views.delete_student, name="delete_student"),
    path('categories/', views.category_list, name="category_list"),
    path('categories/add/', views.add_category, name="add_category"),
    path('categories/edit/<int:category_id>/', views.edit_category, name="edit_category"),
    path('categories/delete/<int:category_id>/', views.delete_category, name="delete_category"),
    path('menu/', views.menu_list, name="menu_list"),
    path('menu/add/', views.add_menu, name="add_menu"),
    path('menu/edit/<int:menu_id>/', views.edit_menu, name="edit_menu"),
    path('menu/delete/<int:menu_id>/', views.delete_menu, name="delete_menu"),
]