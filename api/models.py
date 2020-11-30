import shortuuid
from django.db import models


# Create your models here.
class Log(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='logs', help_text='Log owner.')
    uuid = models.CharField(primary_key=True, max_length=22, editable=False, help_text='Log\'s UUID.')
    created = models.DateTimeField(auto_now_add=True, help_text='Log creation date.')
    expires = models.DateTimeField(null=True, help_text='Log expiration date.')
    content = models.TextField(editable=False, help_text='Raw log content.')
    type = models.CharField(max_length=40, null=True, help_text='Log type.')
    users = models.JSONField(default=list, help_text='List of users in log.')
    privacy = models.CharField(max_length=10, default='public')
    guild = models.BigIntegerField(null=True)
    data = models.JSONField(default=dict, help_text='Extraneous data.')

    class Meta:
        permissions = [
            ('api_access', 'Can access the API'),
            ('extended_expiry', 'Can set an expiry time of up to two weeks'),
            ('no_expiry', 'Can set an infinite expiry time, or none at all')
        ]
        ordering = ['created']

    @classmethod
    def generate_uuid(cls, content):
        """Generate short uuid, used to uniquely identify logs based on content."""
        return shortuuid.uuid(str(content))

    def __str__(self):
        return f'Log {self.uuid}'


class Page(models.Model):
    messages = models.JSONField(editable=False, help_text='Page\'s messages.')
    index = models.IntegerField(editable=False, help_text='Page index.')
    log = models.ForeignKey('Log', editable=False, on_delete=models.CASCADE, related_name='pages', help_text='Log')

    def __str__(self):
        return f'Log {self.log.uuid} Page {self.index}'


class Whitelist(models.Model):
    log_type = models.CharField(max_length=40, help_text='Whitelisted log type.')
    users = models.ManyToManyField('auth.User', related_name='whitelists', help_text='User whitelists.', blank=True)

    def __str__(self):
        return f'{self.log_type.capitalize()} Whitelist'
