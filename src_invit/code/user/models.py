from django.db import models
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your models here.
class User(models.Model):
    class Meta:
        db_table = 'invitusers'

    user_id = models.BigIntegerField(null=True)
    auth_token = models.TextField()
    auth_secret = models.TextField()
    phone_no = models.TextField(unique=True)
    device_id =  models.TextField(null=True)
    name = models.TextField()
    sex = models.CharField(max_length=6, default='', null=True)
    dob = models.DateField(auto_now=False, auto_now_add=False, null=True)
    first_login = models.DateTimeField(null=True)
    last_login = models.DateTimeField(auto_now=True, null=True)

#XXX: For now storing access_tokens in DB to maintain login state.
#TODO: see if this is efficient? Need to move to a caching layer like
# memcache or redis?
class LoginCache(models.Model):
    user_hash = models.TextField(unique=True)
    user_id = models.BigIntegerField(primary_key=True)
