"""
    Login module for twitter digits authentication for invit.
"""
import os
import logging
from datetime import datetime
import tweepy
import hashlib

# Get an instance of a logger
logger = logging.getLogger(__name__)
from code.user.models import User, LoginCache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from code.utils.generic_utils import set_return_response

TWITTER_CONSUMER_KEY = str(os.environ.get('TW_DIG_CONSUMER_KEY'))
TWITTER_CONSUMER_SECRET = str(os.environ.get('TW_DIG_CONSUMER_SECRET'))


def is_user_logged_in(access_token):
    logger.debug("Access_token: "+access_token)
    try:
        cache = LoginCache.objects.get(user_hash=access_token)
    except LoginCache.DoesNotExist as err:
        logger.debug("User with access_token: "+str(access_token)+" does not exist")
        return None
    return cache.user_id

@csrf_exempt
def logout_user(request):
    """
        Log the user out by removing the session variables.
    """
    if 'access_token' in request.POST:
        try:
            cache = LoginCache.objects.get(user_hash=request.POST['access_token'])
        except:
            pass
        else:
            logger.debug("Logging out user with user id: "+str(cache.user_id))
            cache.delete()
    else:
        
        res = {
                'status' : 'error',
                'error_code' : -1,
                'error_msg': 'User not logged in',
                'data': ''
        }
        logger.debug("User not logged in")
        return JsonResponse(res)

    
    res = {
            'status' : 'success',
            'error_code' : 0,
            'error_msg': '',
            'data': ''
    }
    return JsonResponse(res)
    

def set_user_session(request, user):
    """
        Method to set the user information in the session
    """
    #Generate an access token for this user and send it back
    user_hash = hashlib.sha224(user.user_id).hexdigest()
    cache = LoginCache()
    cache.user_hash = user_hash
    cache.user_id = user.user_id
    cache.save()
    return user_hash
    
def validate_user(user_id, auth_token, auth_secret):
    """
        Method that validates the twitter digits user using
        the tweepy api.
    """
    consumer_key = TWITTER_CONSUMER_KEY
    consumer_secret = TWITTER_CONSUMER_SECRET
    auth = tweepy.OAuthHandler(unicode(consumer_key), unicode(consumer_secret))
    auth.secure = True
    auth.set_access_token(auth_token.encode('unicode-escape'), auth_secret.encode('unicode-escape'))
    api = tweepy.API(auth)
    try:
        user = api.verify_credentials()
    except tweepy.error.TweepError as err:
        logger.error("Error while verifying user token for userid "
                     +str(user_id)+"\n"+str(err))
        return False
    if user:
        if user.id_str == unicode(user_id):
            return True
    return False

#Vinay:TODO Is csrf_exempt ok in this case?
@csrf_exempt
def login_user(request):
    """
        Method to login a user using the twitter digits
        authentication.
    """
    res = {
            'status' : 'success',
            'error_code' : 0,
            'error_msg': '',
            'data': ''
    }
    if request.method == 'POST':
        try:
            user_id = request.POST['user_id']
            auth_token = request.POST['auth_token']
            auth_secret = request.POST['auth_secret']
            phone_no = request.POST['phone_no']
            device_id = request.POST['device_id']
            name = request.POST['name']
            #These fields are optional for now
            sex = request.POST['sex'] if 'sex' in request.POST else None
            dob = request.POST['dob'] if 'dob' in request.POST else None
        except KeyError as err:
            logger.error("KeyError during login: "+str(err))
            set_return_response(res, "failed", -1, "Key Error: "+str(err))
            return JsonResponse(res)

        logger.debug('Got a login request with token '+str(auth_token)+'\n')

        #Validate the tokens and the user information
        if ( not validate_user(user_id, auth_token, auth_secret)):
            logger.error("Failed to verify user : "+str(user_id))
            set_return_response(res, "failed", -1,
                "Could not verify user "+str(user_id))
            return JsonResponse(res)
           
        user = None
        try:
            prev_user_entry = User.objects.get(user_id=user_id)
            logger.debug("User "+str(user_id)+" already exists. Updating...\n")
            #Previously logged in user.
            user = User(id=prev_user_entry.id,
                        user_id=user_id,
                        auth_token=auth_token,
                        auth_secret=auth_secret,
                        phone_no=phone_no,
                        device_id=device_id,
                        name=name,
                        sex=sex,
                        dob=dob,
                        first_login=prev_user_entry.first_login)
        except User.DoesNotExist as err:
            #Check if user has been added by someone else before. The phone_no 
            #would be saved
            try:
                added_user_entry = User.objects.get(phone_no=phone_no)
                logger.debug("User with phone "+str(phone_no)+" already added. Updating...\n")
                #Previously added user.
                user = User(id=added_user_entry.id,
                            user_id=user_id,
                            auth_token=auth_token,
                            auth_secret=auth_secret,
                            phone_no=phone_no,
                            device_id=device_id,
                            name=name,
                            sex=sex,
                            dob=dob,
                            first_login=datetime.now())
            except User.DoesNotExist as err:
                #new user
                logger.debug("User "+str(user_id)+" logging in for first time\n")
                user = User(user_id=user_id,
                            auth_token=auth_token,
                            auth_secret=auth_secret,
                            phone_no=phone_no,
                            device_id=device_id,
                            name=name,
                            sex=sex,
                            dob=dob,
                            first_login=datetime.now())
        except Exception as err:
            logger.error("Error while saving user data during login\n"+str(err))
            res['status_msg'] = "Generic error while saving user data"
            set_return_response(res, "failed", -1,
                "DB error while saving user data")
            return JsonResponse(res)
        finally:
            if user:
                try:
                    user.save()
                except Exception as err:
                    set_return_response(res, "failed", -1, str(err), None)
                    return JsonResponse(res)
    
    data = {}
    data['access_token'] = set_user_session(request, user)
    set_return_response(res, "success", 0, "User logged in!", data)
    return JsonResponse(res)
