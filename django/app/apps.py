from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self):
        from kubernetes import config

        config.load_kube_config()
