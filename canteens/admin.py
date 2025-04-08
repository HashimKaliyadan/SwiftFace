from django.contrib import admin
from canteens.models import Student, Menu, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)
    ordering = ('category', 'name')
    fieldsets = (
        ("Menu Details", {'fields': ('name', 'category', 'price', 'is_available', 'image')}),
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'parent', 'parent_phone', 'balance', 'user')
    search_fields = ('student_id', 'name', 'parent__email', 'parent_phone')
    list_filter = ('balance',)
    ordering = ('student_id',)
    readonly_fields = ('student_id',)

    fieldsets = (
        ("Student Details", {'fields': ('student_id', 'name', 'face_image')}),
        ("Parent Information", {'fields': ('parent', 'parent_phone')}),
        ("Account Information", {'fields': ('user', 'balance')}),
    )

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

admin.site.site_header = "Administration"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome"