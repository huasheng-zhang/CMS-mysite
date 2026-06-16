# news/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from news.models import (
    NewsCategory, NewsArticle, ArticleLike,
    ArticleComment, ArticleReadRecord, NewsIndexPage
)
from home.models import HomePage
from wagtail.models import Page

User = get_user_model()

# 测试用中间件配置（移除 AutoLoginMiddleware）
TEST_MIDDLEWARE = [
    m for m in [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "wagtail.contrib.redirects.middleware.RedirectMiddleware",
        "news.middleware.ReadTrackingMiddleware",
        "allauth.account.middleware.AccountMiddleware",
    ]
]


class NewsCategoryModelTest(TestCase):
    def test_create_category(self):
        category = NewsCategory.objects.create(
            name='技术',
            slug='tech',
            description='技术类文章',
            color='#3498db',
            order=1
        )
        self.assertEqual(str(category), '技术')
        self.assertEqual(category.slug, 'tech')


def get_or_create_page_tree():
    """获取或创建 Wagtail 页面树，避免 slug 冲突"""
    home_page = HomePage.objects.first()
    if home_page is None:
        root_page = Page.get_first_root_node()
        home_page = HomePage(title='Home', slug='home')
        root_page.add_child(instance=home_page)

    index_page = NewsIndexPage.objects.first()
    if index_page is None:
        index_page = NewsIndexPage(title='新闻', slug='news-index')
        home_page.add_child(instance=index_page)

    return home_page, index_page


class NewsArticleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = NewsCategory.objects.create(
            name='测试分类',
            slug='test-category'
        )
        _, self.index_page = get_or_create_page_tree()

    def test_create_article(self):
        article = NewsArticle(
            title='测试文章',
            slug='test-article',
            intro='这是一篇测试文章',
            content='测试内容',
            status='published',
            author=self.user,
            category=self.category,
        )
        self.index_page.add_child(instance=article)
        self.assertEqual(article.title, '测试文章')
        self.assertEqual(article.status, 'published')

    def test_article_counts(self):
        article = NewsArticle(
            title='计数测试',
            slug='count-test',
            content='测试内容',
            status='published',
            author=self.user,
        )
        self.index_page.add_child(instance=article)

        self.assertEqual(article.get_read_count(), 0)
        self.assertEqual(article.get_like_count(), 0)
        self.assertEqual(article.get_comment_count(), 0)

        ArticleLike.objects.create(article=article, user=self.user)
        self.assertEqual(article.get_like_count(), 1)

        ArticleComment.objects.create(
            article=article,
            user=self.user,
            content='测试评论',
            is_approved=True
        )
        self.assertEqual(article.get_comment_count(), 1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class NewsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_news_home_public(self):
        """新闻首页应可公开访问"""
        response = self.client.get(reverse('news_home'))
        self.assertEqual(response.status_code, 200)

    def test_news_list_public(self):
        """新闻列表页应可公开访问"""
        response = self.client.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_article_requires_login(self):
        """创建文章需要登录"""
        response = self.client.get(reverse('create_news_article'))
        self.assertIn(response.status_code, [301, 302])

    def test_create_article_authenticated(self):
        """登录用户可以访问创建文章页面"""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('create_news_article'))
        self.assertEqual(response.status_code, 200)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class ArticleCommentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        _, self.index_page = get_or_create_page_tree()

        self.article = NewsArticle(
            title='评论测试',
            slug='comment-test',
            content='测试内容',
            status='published',
            author=self.user,
            allow_comments=True,
        )
        self.index_page.add_child(instance=self.article)

    def test_approved_comment_counted(self):
        """已审核的评论应计入评论数"""
        ArticleComment.objects.create(
            article=self.article,
            user=self.user,
            content='已通过评论',
            is_approved=True
        )
        ArticleComment.objects.create(
            article=self.article,
            user=self.user,
            content='未通过评论',
            is_approved=False
        )
        self.assertEqual(self.article.get_comment_count(), 1)


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class LikeArticleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        _, self.index_page = get_or_create_page_tree()
        self.article = NewsArticle(
            title='点赞测试',
            slug='like-test',
            content='测试内容',
            status='published',
            author=self.user,
            allow_likes=True,
        )
        self.index_page.add_child(instance=self.article)

    def test_like_requires_login(self):
        """点赞需要登录"""
        response = self.client.post(
            reverse('like_article', kwargs={'slug': 'like-test'})
        )
        self.assertIn(response.status_code, [301, 302])

    def test_like_toggle(self):
        """点赞/取消点赞切换"""
        self.client.login(username='test@example.com', password='testpass123')

        # 第一次点赞
        response = self.client.post(
            reverse('like_article', kwargs={'slug': 'like-test'})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)

        # 取消点赞
        response = self.client.post(
            reverse('like_article', kwargs={'slug': 'like-test'})
        )
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)
