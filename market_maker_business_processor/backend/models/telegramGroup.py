from django.db import models
        
class TelegramGroup(models.Model):
    name = models.CharField(max_length=100)
    group_id = models.CharField(max_length=100)
    auth_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    version = models.IntegerField(default=1, editable=False)
          
    class Meta:
        db_table = 'TELEGRAM_GROUPS'