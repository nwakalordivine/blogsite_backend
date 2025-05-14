from django.apps import AppConfig

class BlogapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blogapi'

    def ready(self):
        # Import signals to hook into model save actions, such as profile creation
        import blogapi.signals

        # Ensure any tasks related to signals are set up when the app is ready.
