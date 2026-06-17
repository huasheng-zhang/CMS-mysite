# internal_auth/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'internal_auth'

urlpatterns = [
    # 登录页面
    path('login/', auth_views.LoginView.as_view(template_name='internal_auth/login.html'), name='login'),
    # 注销页面 — 使用自定义视图（同时支持 GET/POST，绕过 LogoutView 硬编码限制）
    path('logout/', views.logout_view, name='logout'),
    # 密码重置
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # 用户资料页面
    path('profile/', views.profile_view, name='profile'),
    # 用户注册页面
    path('register/', views.register_view, name='register'),
]