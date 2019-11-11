from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self):
        from kubernetes import config
        from django.conf import settings
        import os
        import yaml
        from .kube import launch_delete_job

        config.load_kube_config()

        path = os.path.join(settings.DATA_PATH, "bio-node")
        if not settings.DEBUG and not os.path.exists(path):
            yaml_dir = settings.BASE_DIR
            yaml_dir = os.path.join(yaml_dir, "kube_templates")
            yaml_dir = os.path.join(yaml_dir, "bio-node.yml")
            body = yaml.safe_load(yaml_dir)
            launch_delete_job(body)
