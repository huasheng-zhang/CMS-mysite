# news/middleware.py
from django.utils import timezone
from .models import ArticleReadRecord
import logging

logger = logging.getLogger(__name__)


class ReadTrackingMiddleware:
    """统一的阅读记录追踪中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 只跟踪文章页面的阅读（由 news_detail 视图设置 request.article）
        if hasattr(request, 'article') and request.user.is_authenticated:
            # 使用 session 标记避免同一会话重复记录
            session_key = f'read_article_{request.article.id}'
            if not request.session.get(session_key):
                request.session[session_key] = True
                request.session.modified = True

                try:
                    ArticleReadRecord.objects.create(
                        article=request.article,
                        user=request.user,
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
                    )
                    logger.debug(
                        f'记录阅读: 用户 {request.user.username} '
                        f'阅读了 {request.article.title}'
                    )
                except Exception as e:
                    logger.error(f'阅读记录创建失败: {e}')

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        # 基本IP地址格式验证
        if ip and len(ip) > 45:  # IPv6 max length
            ip = ip[:45]
        return ip
