# news/api.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import NewsArticle, ArticleLike, ArticleComment
from django.urls import path, include
from rest_framework.routers import DefaultRouter


class ArticleInteractionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        article = get_object_or_404(NewsArticle, pk=pk)

        with transaction.atomic():
            like, created = ArticleLike.objects.get_or_create(
                article=article,
                user=request.user
            )

            if not created:
                like.delete()
                liked = False
            else:
                liked = True

            count = ArticleLike.objects.filter(article=article).count()
            return Response({
                'liked': liked,
                'count': count
            })

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        article = get_object_or_404(NewsArticle, pk=pk)

        if not article.allow_comments:
            return Response(
                {'error': '该文章不允许评论'},
                status=status.HTTP_403_FORBIDDEN
            )

        content = request.data.get('content', '').strip()

        if len(content) < 5:
            return Response(
                {'error': '评论内容至少5个字符'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(content) > 1000:
            return Response(
                {'error': '评论内容不能超过1000个字符'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = ArticleComment.objects.create(
            article=article,
            user=request.user,
            content=content
        )

        comment_count = ArticleComment.objects.filter(
            article=article,
            is_approved=True
        ).count()

        return Response({
            'id': comment.id,
            'content': comment.content,
            'user': request.user.username or request.user.first_name,
            'created_at': comment.created_at.isoformat(),
            'count': comment_count
        })


# 路由配置
router = DefaultRouter()
router.register(r'news', ArticleInteractionViewSet, basename='news')

urlpatterns = [
    path('v1/', include(router.urls)),
]
