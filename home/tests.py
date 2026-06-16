from home.models import HomePage

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase
from django.test import override_settings

# 测试用中间件配置（移除 AutoLoginMiddleware）
TEST_MIDDLEWARE = [
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


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_exists(self):
        """验证迁移创建的首页存在"""
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """使用迁移创建的首页"""
        self.homepage = HomePage.objects.first()
        if self.homepage is None:
            root_page = Page.get_first_root_node()
            self.homepage = HomePage(title="Home", slug="home")
            root_page.add_child(instance=self.homepage)
            Site.objects.create(
                hostname="testsite",
                root_page=self.homepage,
                is_default_site=True
            )

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")
