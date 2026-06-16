# internal_auth/admin.py
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户资料'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'department', 'position', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'department')

    # 自定义字段布局适配 CustomUser
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('department', 'position', 'employee_id', 'phone', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {'fields': ('email', 'department', 'position', 'employee_id', 'phone')}),
    )


# 先注销再注册，避免冲突；如果未注册则忽略
try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'position', 'employee_id']
    list_filter = ['department', 'position']
    search_fields = ['user__username', 'user__email', 'employee_id']
    readonly_fields = ['user']
