from django.db import models, transaction


class ResourceUsage(models.Model):
    name = models.CharField(max_length=36, blank=True, default="")
    num = models.CharField(max_length=8, blank=True, default="")
    pod = models.CharField(max_length=5, blank=True, default="")

    cpu = models.FloatField(default=-1.0)
    memory = models.FloatField(default=-1.0)

    @classmethod
    def update(cls, combined_name, cpu, memory):
        name = combined_name[:36]
        combined_name = combined_name[37:].split("-")
        if len(combined_name) > 1:
            num = "-".join(combined_name[:-1])
        else:
            num = ""
        pod = combined_name[-1]

        with transaction.atomic():
            try:
                res = cls.objects.get(name=name, num=num, pod=pod)
            except:
                res = cls(name=name, num=num, pod=pod)

            if res.cpu < cpu:
                res.cpu = cpu
            if res.memory < memory:
                res.memory = memory
            res.save()
