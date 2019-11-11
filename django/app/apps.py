from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self):
        import os
        from kubernetes import config

        if os.environ.get("RUN_MAIN", None) != "true":
            return

        config.load_kube_config()

        from django.conf import settings
        import yaml
        from .kube import launch_delete_job

        path = os.path.join(settings.DATA_PATH, "bio-node")
        if not os.path.exists(path):
            os.mkdir(path)
            print("Copying bio-node ...")
            yaml_dir = settings.BASE_DIR
            yaml_dir = os.path.join(yaml_dir, "kube_templates")
            yaml_dir = os.path.join(yaml_dir, "bio-node.yml")
            with open(yaml_dir, "r") as f:
                body = yaml.safe_load(f)
            launch_delete_job(body)
