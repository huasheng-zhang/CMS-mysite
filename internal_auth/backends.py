# internal_auth/backends.py
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class OABackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 开发环境：直接返回用户
        if settings.DEBUG:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        # 生产环境：调用企业IAM接口
        # 这里暂时返回None，开发环境使用Django默认认证
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None