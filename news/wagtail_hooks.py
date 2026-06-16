# news/wagtail_hooks.py
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register
from .models import NewsArticle, NewsCategory, ArticleReadRecord, ArticleLike, ArticleComment
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class NewsArticleAdmin(ModelAdmin):
    model = NewsArticle
    menu_label = _('新闻文章')
    menu_icon = 'doc-full-inverse'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('title', 'author', 'category', 'publish_date', 'status', 'is_featured',
                    'get_read_count', 'get_like_count', 'get_comment_count')
    list_filter = ('category', 'tags', 'publish_date', 'author', 'status', 'is_featured')
    search_fields = ('title', 'intro', 'content')

    def get_read_count(self, obj):
        return obj.get_read_count()
    get_read_count.short_description = _('阅读量')

    def get_like_count(self, obj):
        return obj.get_like_count()
    get_like_count.short_description = _('点赞数')

    def get_comment_count(self, obj):
        return obj.get_comment_count()
    get_comment_count.short_description = _('评论数')


modeladmin_register(NewsArticleAdmin)


class NewsCategoryAdmin(ModelAdmin):
    model = NewsCategory
    menu_label = _('新闻分类')
    menu_icon = 'folder-inverse'
    menu_order = 201
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'slug', 'order', 'color')
    search_fields = ('name', 'slug')


modeladmin_register(NewsCategoryAdmin)


class ArticleReadRecordAdmin(ModelAdmin):
    model = ArticleReadRecord
    menu_label = _('阅读记录')
    menu_icon = 'view'
    menu_order = 202
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('article', 'user', 'read_at', 'read_duration', 'is_completed')
    list_filter = ('read_at', 'is_completed', 'article')
    search_fields = ('article__title', 'user__username', 'user__email')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')


modeladmin_register(ArticleReadRecordAdmin)


class ArticleLikeAdmin(ModelAdmin):
    model = ArticleLike
    menu_label = _('点赞记录')
    menu_icon = 'plus-inverse'
    menu_order = 203
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('article', 'user', 'liked_at')
    list_filter = ('liked_at', 'article')
    search_fields = ('article__title', 'user__username', 'user__email')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')


modeladmin_register(ArticleLikeAdmin)


class ArticleCommentAdmin(ModelAdmin):
    model = ArticleComment
    menu_label = _('评论管理')
    menu_icon = 'snippet'
    menu_order = 204
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('article', 'user', 'content_preview', 'created_at', 'is_approved')
    list_filter = ('created_at', 'is_approved', 'article')
    search_fields = ('article__title', 'user__username', 'user__email', 'content')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('内容预览')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')


modeladmin_register(ArticleCommentAdmin)
