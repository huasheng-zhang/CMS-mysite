# news/management/commands/init_site.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from wagtail.models import Locale, Page, Site
from home.models import HomePage
from news.models import NewsIndexPage


User = get_user_model()


class Command(BaseCommand):
    help = '初始化CMS站点：创建Locale、NewsIndexPage等基础数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='同时创建超级用户',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n开始初始化CMS站点...\n'))

        # 1. 确保 LANGUAGE_CODE 对应的 Locale 存在
        lang = settings.LANGUAGE_CODE
        locale, created = Locale.objects.get_or_create(language_code=lang)
        if created:
            self.stdout.write(self.style.SUCCESS(f'  [OK] 创建 Locale: {lang}'))
        else:
            self.stdout.write(f'  [OK] Locale 已存在: {lang}')

        # 2. 确保 HomePage 存在
        home_page = HomePage.objects.first()
        if not home_page:
            root_page = Page.get_first_root_node()
            home_page = HomePage(title='首页', slug='home')
            root_page.add_child(instance=home_page)
            self.stdout.write(self.style.SUCCESS('  [OK] 创建 HomePage'))

            # 创建默认 Site
            site, _ = Site.objects.get_or_create(
                is_default_site=True,
                defaults={'hostname': 'localhost', 'root_page': home_page}
            )
            self.stdout.write(self.style.SUCCESS(f'  [OK] 默认 Site: {site.hostname}'))
        else:
            self.stdout.write(f'  [OK] HomePage 已存在: {home_page.title}')

        # 3. 确保 NewsIndexPage 存在
        index_page = NewsIndexPage.objects.first()
        if not index_page:
            index_page = NewsIndexPage(
                title='新闻',
                slug='news',
                intro='所有新闻文章',
            )
            home_page.add_child(instance=index_page)
            self.stdout.write(self.style.SUCCESS('  [OK] 创建 NewsIndexPage'))
        else:
            self.stdout.write(f'  [OK] NewsIndexPage 已存在: {index_page.title}')

        # 4. 可选：创建超级用户
        if options['create_superuser']:
            if not User.objects.filter(is_superuser=True).exists():
                admin = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                )
                self.stdout.write(self.style.SUCCESS(
                    f'  [OK] 创建超级用户: {admin.email} (密码: admin123)'
                ))
                self.stdout.write(self.style.WARNING(
                    '  ⚠ 请立即修改默认密码！'
                ))
            else:
                self.stdout.write('  [OK] 超级用户已存在')

        self.stdout.write(self.style.SUCCESS('\n初始化完成！'))
