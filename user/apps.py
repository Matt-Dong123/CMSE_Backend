from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'user'
    verbose_name = "用户"
