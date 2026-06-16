# news/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from django.db import transaction
from django.core.cache import cache
from django.contrib import messages
from django.utils import timezone
from taggit.models import Tag
from .models import NewsArticle, NewsCategory, NewsIndexPage, ArticleLike, ArticleComment, UserFollow, CategorySubscription, TagSubscription
from .forms import NewsArticleForm
import logging
import re

logger = logging.getLogger(__name__)

CACHE_CATEGORIES_KEY = 'news_categories'
CACHE_CATEGORIES_TIMEOUT = 300  # 5 minutes


def ensure_wagtail_locale():
    """确保 LANGUAGE_CODE 对应的 Wagtail Locale 存在"""
    from django.conf import settings
    from wagtail.models import Locale

    lang = getattr(settings, 'LANGUAGE_CODE', 'en')
    if not Locale.objects.filter(language_code=lang).exists():
        Locale.objects.create(language_code=lang)


def get_cached_categories():
    """获取缓存的分类列表"""
    categories = cache.get(CACHE_CATEGORIES_KEY)
    if categories is None:
        categories = list(NewsCategory.objects.annotate(
            article_count=Count(
                'articles',
                filter=Q(articles__status='published') &
                       (Q(articles__publish_date__lte=timezone.now()) |
                        Q(articles__publish_date__isnull=True))
            )
        ))
        cache.set(CACHE_CATEGORIES_KEY, categories, CACHE_CATEGORIES_TIMEOUT)
    return categories


def news_list(request):
    """新闻列表页面"""
    articles = NewsArticle.objects.with_counts().published().select_related(
        'author', 'category'
    ).prefetch_related('tagged_items__tag').order_by('-publish_date')

    # 获取筛选参数
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')

    if category_id:
        articles = articles.filter(category_id=category_id)

    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(intro__icontains=search_query)
        )

    # 分页
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = get_cached_categories()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'search_query': search_query,
    }
    return render(request, 'news/news_list.html', context)


def news_detail(request, slug):
    """新闻详情页面"""
    article = get_object_or_404(
        NewsArticle.objects.with_counts().select_related('author', 'category').prefetch_related('tagged_items__tag'),
        slug=slug,
        status='published'
    )

    # 阅读记录由 ReadTrackingMiddleware 统一处理，此处不再重复记录

    # 获取相关文章
    related_articles = NewsArticle.objects.with_counts().published().select_related(
        'author', 'category'
    ).prefetch_related('tagged_items__tag').filter(
        category=article.category,
    ).exclude(id=article.id)[:5] if article.category else NewsArticle.objects.none()

    # 获取评论
    comments = ArticleComment.objects.filter(
        article=article,
        is_approved=True,
        parent__isnull=True,  # 只获取顶级评论
    ).select_related('user').order_by('-created_at')

    # 检查用户是否点赞
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ArticleLike.objects.filter(
            article=article,
            user=request.user
        ).exists()

    # 将文章对象设置到 request 上，供 ReadTrackingMiddleware 使用
    request.article = article

    context = {
        'article': article,
        'related_articles': related_articles,
        'comments': comments,
        'user_liked': user_liked,
    }
    return render(request, 'news/news_detail.html', context)


@login_required
def create_news_article(request):
    """创建新闻文章 - 使用 Wagtail add_child API 正确创建页面树节点"""
    if request.method == 'POST':
        ensure_wagtail_locale()
        form = NewsArticleForm(request.POST, request.FILES)
        if form.is_valid():
            # 获取 NewsIndexPage 作为父页面（Wagtail 页面树要求）
            index_page = NewsIndexPage.objects.live().first()
            if not index_page:
                messages.error(request, '系统尚未初始化新闻列表页，请联系管理员。')
                return redirect('news_home')

            # 手动从表单数据构建文章实例（不使用 form.save，避免 Locale 缺失）
            raw_slug = form.cleaned_data.get('slug') or form.cleaned_data['title']
            # 确保 slug 唯一性：如果已存在则追加数字后缀
            unique_slug = raw_slug
            counter = 1
            while NewsArticle.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{raw_slug}-{counter}'
                counter += 1

            article = NewsArticle(
                title=form.cleaned_data['title'],
                slug=unique_slug,
                intro=form.cleaned_data.get('intro', ''),
                content=form.cleaned_data.get('content', ''),
                category=form.cleaned_data.get('category'),
                status=form.cleaned_data.get('status', 'draft'),
                is_featured=form.cleaned_data.get('is_featured', False),
                publish_date=form.cleaned_data.get('publish_date'),
                image=form.cleaned_data.get('image'),
                author=request.user,
            )

            # 处理 tags（ClusterTaggableManager 需要先保存页面再设置标签）
            tags_value = form.cleaned_data.get('tags', '')

            # 通过 Wagtail 页面树 API 添加子页面（自动设置 path, depth, locale）
            index_page.add_child(instance=article)

            # 页面保存后设置 tags
            if tags_value:
                if isinstance(tags_value, str):
                    tag_list = [t.strip() for t in tags_value.split(',') if t.strip()]
                else:
                    tag_list = [str(t).strip() for t in tags_value if str(t).strip()]
                if tag_list:
                    article.tags.set(tag_list)
                    article.save()

            # 清除分类缓存
            cache.delete(CACHE_CATEGORIES_KEY)
            messages.success(request, '文章发布成功！')
            logger.info(f'用户 {request.user.username} 发布了新文章: {article.title}')
            return redirect('news_detail', slug=article.slug)
        else:
            messages.error(request, '表单填写有误，请检查后重新提交。')
    else:
        form = NewsArticleForm()

    context = {
        'form': form,
    }
    return render(request, 'news/create_article.html', context)


@login_required
def edit_news_article(request, slug):
    """编辑新闻文章"""
    article = get_object_or_404(NewsArticle, slug=slug)

    # 只有作者或管理员才能编辑
    if article.author != request.user and not request.user.is_staff:
        messages.error(request, '您没有权限编辑此文章。')
        return redirect('news_detail', slug=slug)

    if request.method == 'POST':
        form = NewsArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            # 编辑时文章已在页面树中，直接保存更新字段
            updated_article = form.save(commit=False)

            # 处理 tags
            tags_value = form.cleaned_data.get('tags', '')
            if tags_value is not None:
                if isinstance(tags_value, str):
                    tag_list = [t.strip() for t in tags_value.split(',') if t.strip()]
                else:
                    tag_list = [str(t).strip() for t in tags_value if str(t).strip()]
                updated_article.tags.set(tag_list) if tag_list else updated_article.tags.clear()

            updated_article.save()
            cache.delete(CACHE_CATEGORIES_KEY)
            messages.success(request, '文章更新成功！')
            return redirect('news_detail', slug=article.slug)
        else:
            messages.error(request, '表单填写有误，请检查后重新提交。')
    else:
        form = NewsArticleForm(instance=article)

    context = {
        'form': form,
        'article': article,
    }
    return render(request, 'news/edit_article.html', context)


@login_required
def like_article(request, slug):
    """点赞/取消点赞文章"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    article = get_object_or_404(NewsArticle, slug=slug)

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
        like_count = ArticleLike.objects.filter(article=article).count()

    return JsonResponse({
        'liked': liked,
        'like_count': like_count
    })


@login_required
def add_comment(request, slug):
    """添加评论"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    article = get_object_or_404(NewsArticle, slug=slug)

    if not article.allow_comments:
        return JsonResponse({'success': False, 'error': '该文章不允许评论'}, status=403)

    raw_content = request.POST.get('content', '').strip()
    # Strip HTML tags to prevent stored XSS
    content = re.sub(r'<[^>]+>', '', raw_content).strip()
    if len(content) < 2:
        return JsonResponse({'success': False, 'error': '评论内容至少2个字符'}, status=400)

    if len(content) > 1000:
        return JsonResponse({'success': False, 'error': '评论内容不能超过1000个字符'}, status=400)

    comment = ArticleComment.objects.create(
        article=article,
        user=request.user,
        content=content
    )

    comment_count = ArticleComment.objects.filter(
        article=article,
        is_approved=True
    ).count()

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        },
        'comment_count': comment_count,
    })


def news_home(request):
    """新闻首页 - 支持双Tab: 最新 / 关注"""
    tab = request.GET.get('tab', 'latest')
    categories = get_cached_categories()

    # 最新文章（默认）
    latest_articles = NewsArticle.objects.with_counts().published().select_related(
        'author', 'category'
    ).prefetch_related('tagged_items__tag').order_by('-publish_date')[:6]

    featured_articles = NewsArticle.objects.with_counts().published().select_related(
        'author', 'category'
    ).prefetch_related('tagged_items__tag').filter(
        is_featured=True
    ).order_by('-publish_date')[:3]

    popular_articles = NewsArticle.objects.with_counts().published().select_related(
        'author', 'category'
    ).prefetch_related('tagged_items__tag').order_by('-_read_count')[:5]

    # 个性化Feed（关注Tab）
    feed_articles = []
    if request.user.is_authenticated and tab == 'following':
        following_ids = UserFollow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        subscribed_category_ids = CategorySubscription.objects.filter(
            user=request.user
        ).values_list('category_id', flat=True)

        subscribed_tag_ids = TagSubscription.objects.filter(
            user=request.user
        ).values_list('tag_id', flat=True)

        feed_articles = NewsArticle.objects.with_counts().published().select_related(
            'author', 'category'
        ).prefetch_related('tagged_items__tag').filter(
            Q(author_id__in=following_ids) |
            Q(category_id__in=subscribed_category_ids) |
            Q(tags__id__in=subscribed_tag_ids)
        ).order_by('-publish_date').distinct()[:6]

    context = {
        'tab': tab,
        'latest_articles': latest_articles,
        'featured_articles': featured_articles,
        'popular_articles': popular_articles,
        'feed_articles': feed_articles,
        'categories': categories,
    }
    return render(request, 'news/home.html', context)


@login_required
def follow_author(request, user_id):
    """关注/取消关注作者"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        return JsonResponse({'error': '不能关注自己'}, status=400)

    with transaction.atomic():
        follow, created = UserFollow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        if not created:
            follow.delete()
            following = False
        else:
            following = True
        follower_count = UserFollow.objects.filter(following=target_user).count()

    return JsonResponse({
        'following': following,
        'follower_count': follower_count
    })


@login_required
def subscribe_category(request, category_id):
    """订阅/取消订阅分类"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    category = get_object_or_404(NewsCategory, pk=category_id)

    with transaction.atomic():
        sub, created = CategorySubscription.objects.get_or_create(
            user=request.user,
            category=category
        )
        if not created:
            sub.delete()
            subscribed = False
        else:
            subscribed = True
        subscriber_count = CategorySubscription.objects.filter(category=category).count()

    return JsonResponse({
        'subscribed': subscribed,
        'subscriber_count': subscriber_count
    })


@login_required
def subscribe_tag(request, tag_id):
    """订阅/取消订阅标签"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    tag = get_object_or_404(Tag, pk=tag_id)

    with transaction.atomic():
        sub, created = TagSubscription.objects.get_or_create(
            user=request.user,
            tag=tag
        )
        if not created:
            sub.delete()
            subscribed = False
        else:
            subscribed = True
        subscriber_count = TagSubscription.objects.filter(tag=tag).count()

    return JsonResponse({
        'subscribed': subscribed,
        'subscriber_count': subscriber_count
    })
