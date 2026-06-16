from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from news.api import urlpatterns as news_api_urls

urlpatterns = [
    # Django原生admin
    path("django-admin/", admin.site.urls),

    # Wagtail admin
    path("admin/", include(wagtailadmin_urls)),

    # Wagtail文档管理
    path("documents/", include(wagtaildocs_urls)),

    # 搜索功能
    path("search/", search_views.search, name="search"),

    # 用户账户管理 (allauth)
    path('accounts/', include('allauth.urls')),

    # API接口
    path('api/', include(news_api_urls)),

    # 新闻应用
    path('news/', include('news.urls')),

    # 认证应用
    path('auth/', include('internal_auth.urls')),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Wagtail主路由 (必须放在最后，作为兜底路由)
urlpatterns += [
    path("", include(wagtail_urls)),
]
