# news/admin.py
from django.contrib import admin
from .models import NewsArticle, NewsCategory, ArticleReadRecord, ArticleLike, ArticleComment


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'color')
    list_editable = ('order',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ArticleReadRecord)
class ArticleReadRecordAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'read_at', 'read_duration', 'is_completed', 'ip_address')
    list_filter = ('is_completed', 'read_at')
    search_fields = ('article__title', 'user__username', 'user__email')
    readonly_fields = ('article', 'user', 'read_at', 'read_duration', 'is_completed', 'ip_address', 'user_agent')
    date_hierarchy = 'read_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'liked_at')
    list_filter = ('liked_at',)
    search_fields = ('article__title', 'user__username', 'user__email')
    readonly_fields = ('article', 'user', 'liked_at')
    date_hierarchy = 'liked_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'content_preview', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('article__title', 'user__username', 'user__email', 'content')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'
    actions = ['approve_comments', 'disapprove_comments']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '内容预览'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')

    @admin.action(description='批量审核通过')
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'已审核通过 {updated} 条评论。')

    @admin.action(description='批量取消审核')
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'已取消 {updated} 条评论的审核。')
