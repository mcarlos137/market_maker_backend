from django.db import models

class Status(models.IntegerChoices):
    active = 1
    inactive = 2

class Market(models.Model):
    base = models.CharField(max_length=5, null=True)
    quote = models.CharField(max_length=5, null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.active)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)

    def __str__(self):
        return "%s-%s" % (self.base, self.quote)

    class Meta:
        db_table = 'MARKETS'