# news/urls.py
from django.urls import path, register_converter
from . import views


class UnicodeSlugConverter:
    """支持中文等 Unicode 字符的 slug 路由转换器"""
    regex = r'[-\w]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(UnicodeSlugConverter, 'uslug')

urlpatterns = [
    path('', views.news_home, name='news_home'),
    path('list/', views.news_list, name='news_list'),
    path('article/<uslug:slug>/', views.news_detail, name='news_detail'),
    path('create/', views.create_news_article, name='create_news_article'),
    path('edit/<uslug:slug>/', views.edit_news_article, name='edit_news_article'),
    path('like/<uslug:slug>/', views.like_article, name='like_article'),
    path('comment/<uslug:slug>/', views.add_comment, name='add_comment'),
    path('follow/<int:user_id>/', views.follow_author, name='follow_author'),
    path('subscribe/category/<int:category_id>/', views.subscribe_category, name='subscribe_category'),
    path('subscribe/tag/<int:tag_id>/', views.subscribe_tag, name='subscribe_tag'),
    path('upload-image/', views.upload_editor_image, name='upload_editor_image'),
    path('track-read/', views.track_read_progress, name='track_read_progress'),
]