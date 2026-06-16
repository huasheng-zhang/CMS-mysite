# internal_auth/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    """
    自定义用户模型，扩展默认的用户模型
    """
    email = models.EmailField(unique=True)  # 确保邮箱唯一
    department = models.CharField("部门", max_length=100, blank=True)
    position = models.CharField("职位", max_length=100, blank=True)
    employee_id = models.CharField("员工ID", max_length=50, blank=True)
    phone = models.CharField("电话", max_length=20, blank=True)
    avatar = models.ImageField("头像", upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    USERNAME_FIELD = 'email'  # 使用邮箱作为登录字段
    REQUIRED_FIELDS = ['username']  # 必填字段

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """
    用户资料模型
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    department = models.CharField("部门", max_length=100, blank=True)
    position = models.CharField("职位", max_length=100, blank=True)
    employee_id = models.CharField("员工ID", max_length=50, blank=True)
    phone = models.CharField("电话", max_length=20, blank=True)
    avatar = models.ImageField("头像", upload_to='avatars/', blank=True, null=True)
    bio = models.TextField("个人简介", blank=True)
    location = models.CharField("位置", max_length=100, blank=True)
    birth_date = models.DateField("生日", null=True, blank=True)

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self):
        return f"{self.user.username} - Profile"


# 信号处理器
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()