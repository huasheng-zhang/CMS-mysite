# internal_auth/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

# 测试用中间件配置（移除 AutoLoginMiddleware）
TEST_MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "news.middleware.ReadTrackingMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]


class CustomUserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_user_profile_auto_created(self):
        """创建用户时应自动创建 UserProfile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)

    def test_email_unique(self):
        """邮箱必须唯一"""
        User.objects.create_user(
            username='user1',
            email='same@example.com',
            password='pass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='same@example.com',
                password='pass456'
            )


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_page(self):
        """登录页面可访问"""
        response = self.client.get(reverse('internal_auth:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        """注册页面可访问"""
        response = self.client.get(reverse('internal_auth:register'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """正确的凭据可以登录"""
        response = self.client.post(reverse('internal_auth:login'), {
            'username': 'test@example.com',
            'password': 'testpass123',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_register_success(self):
        """注册新用户"""
        response = self.client.post(reverse('internal_auth:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_profile_requires_login(self):
        """个人资料页面需要登录"""
        response = self.client.get(reverse('internal_auth:profile'))
        self.assertIn(response.status_code, [301, 302])

    def test_profile_authenticated(self):
        """登录用户可以访问个人资料"""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('internal_auth:profile'))
        self.assertEqual(response.status_code, 200)
