from django.conf import settings
from django.db import models


class Audit(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField(max_length=1000)
    created = models.DateTimeField(auto_now_add=True)
    results = models.JSONField(default=list)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created"]


class Review(models.Model):
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="reviews")
    criterion = models.CharField(max_length=80)
    status = models.CharField(
        max_length=12,
        choices=[
            ("pending", "Pendiente"),
            ("yes", "Evidenciado"),
            ("no", "No evidenciado"),
            ("na", "No aplica"),
        ],
        default="pending",
    )
    evidence = models.TextField(blank=True, max_length=4000)

    class Meta:
        unique_together = [("audit", "criterion")]


class Event(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=100)
    audit_id_record = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
