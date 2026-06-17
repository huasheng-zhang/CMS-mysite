from django.db import models
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from wagtail.models import Page, PageManager, PageQuerySet
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, Tag


class NewsCategory(models.Model):
    name = models.CharField("分类名称", max_length=100, unique=True)
    slug = models.SlugField("URL标识", unique=True, allow_unicode=True)
    description = models.TextField("描述", blank=True)
    color = models.CharField("颜色", max_length=7, default="#3498db", help_text="分类标签颜色，如 #3498db")
    order = models.IntegerField("排序", default=0)

    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('description'),
        FieldPanel('color'),
        FieldPanel('order'),
    ]

    class Meta:
        verbose_name = "新闻分类"
        verbose_name_plural = "新闻分类"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class NewsTag(TaggedItemBase):
    content_object = ParentalKey(
        'NewsArticle',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class NewsArticleQuerySet(PageQuerySet):
    """自定义查询集，提供带计数的批量查询方法"""

    def with_counts(self):
        """一次性注解阅读数、点赞数、评论数，避免 N+1 查询"""
        return self.annotate(
            _read_count=Count('read_records', distinct=True),
            _like_count=Count('likes', distinct=True),
            _comment_count=Count(
                'comments',
                filter=Q(comments__is_approved=True),
                distinct=True
            ),
        )

    def published(self):
        """返回已发布的文章"""
        from django.utils import timezone
        return self.filter(
            status='published',
        ).filter(
            Q(publish_date__lte=timezone.now()) | Q(publish_date__isnull=True)
        )


class NewsArticleManager(PageManager):
    """自定义管理器"""

    def get_queryset(self):
        return NewsArticleQuerySet(self.model, using=self._db)

    def with_counts(self):
        return self.get_queryset().with_counts()

    def published(self):
        return self.get_queryset().published()


class NewsArticle(Page):
    # 基本信息
    publish_date = models.DateTimeField("发布日期", null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_articles',
        verbose_name="作者"
    )

    # 内容字段
    intro = RichTextField("简介", blank=True, features=['bold', 'italic', 'link'])
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title", icon="title")),
        ('paragraph', blocks.RichTextBlock(features=[
            'h2', 'h3', 'h4', 'bold', 'italic', 'ol', 'ul', 'hr',
            'link', 'document-link', 'image', 'embed'
        ])),
        ('image', ImageChooserBlock()),
        ('video', blocks.RawHTMLBlock(
            icon="media",
            label="视频嵌入",
            help_text="支持HTML5 video标签或第三方视频平台嵌入代码"
        )),
        ('html_content', blocks.RawHTMLBlock(
            icon="code",
            label="HTML内容",
            help_text="支持原始HTML，用于复杂内容展示"
        )),
    ], use_json_field=True, blank=True)

    # 交互功能
    allow_comments = models.BooleanField("允许评论", default=True)
    allow_sharing = models.BooleanField("允许分享", default=True)
    allow_likes = models.BooleanField("允许点赞", default=True)

    # 分类和标签
    category = models.ForeignKey(
        'news.NewsCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name="分类"
    )
    tags = ClusterTaggableManager(through=NewsTag, blank=True, verbose_name="标签")

    # SEO相关
    keywords = models.CharField("关键词", max_length=200, blank=True)

    # 内容字段
    content = models.TextField("内容", blank=True)
    status = models.CharField("状态", max_length=20, choices=[
        ('draft', '草稿'),
        ('published', '已发布'),
    ], default='draft')
    is_featured = models.BooleanField("是否推荐", default=False)
    image = models.ImageField("封面图片", upload_to='news_images/', blank=True, null=True)

    # 搜索索引
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
        index.FilterField('publish_date'),
        index.RelatedFields('category', [
            index.SearchField('name'),
        ]),
        index.RelatedFields('tags', [
            index.SearchField('name'),
        ]),
    ]

    # 后台编辑面板
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('publish_date'),
            FieldPanel('author'),
            FieldPanel('category'),
            FieldPanel('tags'),
            FieldPanel('status'),
            FieldPanel('is_featured'),
            FieldPanel('image'),
        ], heading="文章元数据"),

        MultiFieldPanel([
            FieldPanel('intro'),
            FieldPanel('content'),
            FieldPanel('body'),
        ], heading="内容"),

        MultiFieldPanel([
            FieldPanel('allow_comments'),
            FieldPanel('allow_sharing'),
            FieldPanel('allow_likes'),
        ], heading="交互设置"),

        MultiFieldPanel([
            FieldPanel('keywords'),
        ], heading="SEO设置"),
    ]

    # 页面类型设置
    parent_page_types = ['news.NewsIndexPage']
    subpage_types = []

    # 使用自定义管理器
    objects = NewsArticleManager()

    def save(self, *args, **kwargs):
        # 自动设置作者
        if not self.author and self.owner:
            self.author = self.owner

        # 如果有body内容，同步到content字段
        if hasattr(self, 'body') and self.body:
            self.content = str(self.body)

        # 安全: 过滤content中的危险HTML标签(防止存储型XSS)
        if self.content:
            import re
            # Remove script, iframe, object, embed, form tags and their content
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>',
                r'<form[^>]*>.*?</form>',
                r'\bon\w+\s*=\s*["\'][^"\']*["\']',  # inline event handlers
                r'javascript\s*:',  # javascript: URLs
            ]
            for pattern in dangerous_patterns:
                self.content = re.sub(pattern, '', self.content, flags=re.IGNORECASE | re.DOTALL)

        super().save(*args, **kwargs)

    def get_read_count(self):
        """获取阅读量（优先使用注解值）"""
        if hasattr(self, '_read_count'):
            return self._read_count
        return self.read_records.count()

    def get_like_count(self):
        """获取点赞数（优先使用注解值）"""
        if hasattr(self, '_like_count'):
            return self._like_count
        return self.likes.count()

    def get_comment_count(self):
        """获取评论数（优先使用注解值）"""
        if hasattr(self, '_comment_count'):
            return self._comment_count
        return self.comments.filter(is_approved=True).count()

    class Meta:
        verbose_name = "新闻文章"
        verbose_name_plural = "新闻文章"
        ordering = ['-publish_date']
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]


class ArticleReadRecord(models.Model):
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='read_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='read_records'
    )
    read_at = models.DateTimeField("阅读时间", default=timezone.now)
    read_duration = models.IntegerField("阅读时长(秒)", default=0)
    is_completed = models.BooleanField("是否读完", default=False)
    ip_address = models.GenericIPAddressField("IP地址", null=True, blank=True)
    user_agent = models.TextField("用户代理", blank=True)

    class Meta:
        verbose_name = "阅读记录"
        verbose_name_plural = "阅读记录"
        unique_together = ['article', 'user']
        indexes = [
            models.Index(fields=['article', 'user']),
            models.Index(fields=['read_at']),
        ]


class ArticleLike(models.Model):
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['article', 'user']
        indexes = [models.Index(fields=['article', 'user'])]


class ArticleComment(models.Model):
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField("评论内容")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField("是否审核通过", default=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name="父评论"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'is_approved']),
            models.Index(fields=['article', 'is_approved', '-created_at']),
        ]


class UserFollow(models.Model):
    """用户关注关系"""
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="关注者"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name="被关注者"
    )
    created_at = models.DateTimeField("关注时间", auto_now_add=True)

    class Meta:
        verbose_name = "关注关系"
        verbose_name_plural = "关注关系"
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]


class CategorySubscription(models.Model):
    """分类订阅"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='category_subscriptions',
        verbose_name="用户"
    )
    category = models.ForeignKey(
        'NewsCategory',
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name="分类"
    )
    created_at = models.DateTimeField("订阅时间", auto_now_add=True)

    class Meta:
        verbose_name = "分类订阅"
        verbose_name_plural = "分类订阅"
        unique_together = ['user', 'category']


class TagSubscription(models.Model):
    """标签订阅"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tag_subscriptions',
        verbose_name="用户"
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name="标签"
    )
    created_at = models.DateTimeField("订阅时间", auto_now_add=True)

    class Meta:
        verbose_name = "标签订阅"
        verbose_name_plural = "标签订阅"
        unique_together = ['user', 'tag']


class NewsIndexPage(Page):
    intro = RichTextField("列表页简介", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    parent_page_types = ['home.HomePage', 'wagtailcore.Page']
    subpage_types = ['news.NewsArticle']

    def get_context(self, request):
        context = super().get_context(request)
        articles = NewsArticle.objects.with_counts().filter(
            path__startswith=self.path,
            depth=self.depth + 1,
            live=True,
        ).order_by('-first_published_at')

        from django.core.paginator import Paginator
        paginator = Paginator(articles, 10)
        page_number = request.GET.get('page')
        context['articles'] = paginator.get_page(page_number)

        return context

    class Meta:
        verbose_name = "新闻列表页"
        verbose_name_plural = "新闻列表页"
