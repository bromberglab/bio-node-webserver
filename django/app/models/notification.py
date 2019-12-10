from django.db import models
from django.contrib.auth.models import User
from app.events import send_event


class Notification(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    short_text = models.CharField(max_length=256)
    long_text = models.TextField()
    importance = models.IntegerField(default=5)
    """
    Why is importance an Integer and not a choice field?
    Because it's more flexible.
    Why is the default importance 5?
    Because 5 is info, and the values are so spaced out
    because it's easier for future expansion.
    
    Info: 5
    Warning: 10
    Error: 15
    """

    @classmethod
    def job_finished(cls, job, status, pod_name):
        from .job import Job
        from .workflow import Workflow

        job: Job = job
        workflow: Workflow = job.workflow

        if workflow is None:
            return  # No user to send to.

        user = workflow.user

        if status == "succeeded":
            short_text = "Your job %s finished." % job.display_name
            importance = 5
        else:
            short_text = "Your job %s failed!" % job.display_name
            importance = 15

        long_text = "Status: %s\nSee workflow page for logs." % status

        cls.send(user, short_text, long_text, importance)

    @classmethod
    def send(cls, user, short_text, long_text="", importance=5):
        short_text = short_text[:256]
        long_text = long_text[:100000]  # let's not get too crazy.

        obj = cls(
            user=user, short_text=short_text, long_text=long_text, importance=importance
        )
        obj.save()
        obj.notify()

    def notify(self):
        send_event("notification", {"user": self.user.pk, "id": self.pk})
