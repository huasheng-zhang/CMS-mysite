# internal_auth/middleware.py
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import get_user_model
import re


class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 排除登录相关URL
        exclude_paths = [
            r'^/accounts/',
            r'^/admin/',
            r'^/django-admin/',
            r'^/oauth/',
            r'^/api/',
            r'^/static/',
            r'^/media/',
        ]

        if any(re.match(pattern, request.path) for pattern in exclude_paths):
            return self.get_response(request)

        # 检查是否已登录
        if not request.user.is_authenticated:
            # 开发环境：尝试自动登录为超级用户
            if settings.DEBUG:
                from django.contrib.auth import login

                User = get_user_model()
                superuser = User.objects.filter(is_superuser=True).first()
                if superuser:
                    login(request, superuser, backend='django.contrib.auth.backends.ModelBackend')
                    return redirect(request.path)
                # 没有超级用户时不重定向，允许匿名访问
                return self.get_response(request)

            # 生产环境：重定向到登录页面
            return redirect(f'/auth/login/?next={request.path}')

        return self.get_response(request)
