from django.apps import AppConfig
class InternalAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'internal_auth'

    def ready(self):
        import internal_auth.models  # 导入信号处理器
