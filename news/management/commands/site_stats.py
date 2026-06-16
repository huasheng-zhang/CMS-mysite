# news/management/commands/site_stats.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from news.models import NewsArticle, NewsCategory, ArticleReadRecord, ArticleLike, ArticleComment
from django.db.models import Count, Sum, Q


User = get_user_model()


class Command(BaseCommand):
    help = '显示CMS系统统计数据'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('  CMS新闻管理系统 - 站点统计报告'))
        self.stdout.write(self.style.SUCCESS('=' * 50 + '\n'))

        # 用户统计
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()

        self.stdout.write(self.style.WARNING('【用户统计】'))
        self.stdout.write(f'  总用户数:     {total_users}')
        self.stdout.write(f'  活跃用户:     {active_users}')
        self.stdout.write(f'  管理员:       {staff_users}')

        # 文章统计
        total_articles = NewsArticle.objects.count()
        published = NewsArticle.objects.filter(status='published').count()
        drafts = NewsArticle.objects.filter(status='draft').count()
        featured = NewsArticle.objects.filter(is_featured=True).count()

        self.stdout.write(self.style.WARNING('\n【文章统计】'))
        self.stdout.write(f'  总文章数:     {total_articles}')
        self.stdout.write(f'  已发布:       {published}')
        self.stdout.write(f'  草稿:         {drafts}')
        self.stdout.write(f'  推荐文章:     {featured}')

        # 分类统计
        categories = NewsCategory.objects.annotate(
            article_count=Count('articles')
        ).order_by('-article_count')

        self.stdout.write(self.style.WARNING('\n【分类统计】'))
        if categories:
            for cat in categories:
                self.stdout.write(f'  {cat.name}: {cat.article_count} 篇')
        else:
            self.stdout.write('  暂无分类')

        # 互动统计
        total_reads = ArticleReadRecord.objects.count()
        total_likes = ArticleLike.objects.count()
        total_comments = ArticleComment.objects.count()
        approved_comments = ArticleComment.objects.filter(is_approved=True).count()

        self.stdout.write(self.style.WARNING('\n【互动统计】'))
        self.stdout.write(f'  总阅读量:     {total_reads}')
        self.stdout.write(f'  总点赞数:     {total_likes}')
        self.stdout.write(f'  总评论数:     {total_comments}')
        self.stdout.write(f'  已审核评论:   {approved_comments}')

        # 热门文章 Top 5
        top_articles = NewsArticle.objects.annotate(
            read_count=Count('read_records')
        ).filter(status='published').order_by('-read_count')[:5]

        self.stdout.write(self.style.WARNING('\n【热门文章 Top 5】'))
        for i, article in enumerate(top_articles, 1):
            self.stdout.write(f'  {i}. {article.title} (阅读: {article.read_count})')

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
