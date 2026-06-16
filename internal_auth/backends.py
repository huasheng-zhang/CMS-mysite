# internal_auth/backends.py
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class OABackend:
    """企业IAM认证后端

    开发环境: 通过用户名直接认证(仅限DEBUG=True)
    生产环境: 预留企业IAM接口集成
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if settings.DEBUG:
            logger.warning('OABackend: DEBUG模式认证，仅限开发环境使用')
            try:
                user = User.objects.get(username=username)
                # 即使在DEBUG模式，也验证密码(如果提供了的话)
                if password and not user.check_password(password):
                    logger.warning(f'OABackend: 密码验证失败 - 用户 {username}')
                    return None
                return user
            except User.DoesNotExist:
                return None

        # 生产环境：调用企业IAM接口
        # TODO: 实现企业IAM OAuth2集成
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None