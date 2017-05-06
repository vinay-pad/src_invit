import logging
import pytz
import calendar

from code.user.models import User
from datetime import datetime
from code.utils.generic_utils import set_return_response
from code.event_crud.models import Event, Location, \
                                    LocationPreference, Time, \
                                    TimePreference, LocationLike, \
                                    TimeLike
from django.db import transaction, IntegrityError
from invit.settings import TIME_ZONE
from django.db import transaction
from code.event_crud.exceptions import NoUsersInDB, NoEventInDB

# Get an instance of a logger
logger = logging.getLogger(__name__)

latest_activity = {
    'add_location' : " added a location preference",
    'add_time' : " added a time preference",
    'add_participant' : " added participants",
    'like_location' : " liked a location preference",
    'like_time' : " liked a time preference",
    'lock_time' : " locked time preference",
    'unlock_time' : " unlocked time preference",
    'lock_location' : " locked location preference",
    'unlock_location' : " unlocked location preference",
    'remove_participant' : " removed participant from event"
}

def set_event_latest_activity(event, user, action):
    event.latest_activity = str(user.name)+latest_activity[action]
    
def fetch_event(eventid):
    """
        Helper method to fetch the event
    """
    #Fetch the event first
    try:
        event = Event.objects.get(id=eventid)
    except Event.DoesNotExist, err:
        raise NoEventInDB(err)


    if not event:
        raise NoEventInDB(err)

    return event

def update_event_add_location(event, payload, curr_user):
    """
        Method to add a location preference to an event
        Returns a response in the form of,
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    """
    resp = {}
    try:
        place_id = payload['place_id']
        name = payload['name']
        address = payload['address']
        lat = payload['lat']
        lng = payload['lng']
        service = payload['service']
        phone_no = payload['phone_no']
        rating = payload['rating']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    #If the given place_id for the given service exists, then
    #retrieve it. If not create it.   
    try:
        loc = Location.objects.get(place_id=place_id,
                       service=service)
    except Location.DoesNotExist:
        logger.debug("Location "+str(name)+": "+str(place_id)+", "
                    +str(service)+" does not exist, creating...")
        loc = Location.objects.create(place_id=place_id,
                       name=name,
                       address=address,
                       latitude=lat,
                       longitude=lng,
                       service=service,
                       phone_no=phone_no,
                       rating=rating)
        


    loc_pref = LocationPreference(event=event,
                                  location=loc,
                                  user=curr_user,
                                  created_ts=datetime.now())
    try:
        loc_pref.save()
    except Exception as err:
        #TODO: catch specific errors
        resp['error_code'] = -1
        resp['msg'] = "Error saving location preference "+str(name)+" to event "+str(event.id)+", error: "+str(err)
    else:
        logger.debug("Succesfully added location preference "+str(name)+" to event "+str(event.id))
        resp['error_code'] = 0
        resp['msg'] = "Succesfully added location preference "+str(name)+" to event "+str(event.id)

    return resp

def update_event_add_time(event, payload, curr_user):
    """
        Method to add time preference to the event
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    """
    resp = {}
    try:
        start_ts = payload['start_ts']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    try:
        local_tz = pytz.timezone(TIME_ZONE) 
        utc_dt = datetime.utcfromtimestamp(start_ts).replace(tzinfo=pytz.utc)
        local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))
    except Exception as err:
        logger.error("Error converting unix time "+str(start_ts)+" to datetime,"+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Error converting unix time "+str(start_ts)+" to datetime"
        return resp

    #If the given Time exists then retrive it.
    #If not create it.   
    try:
        time = Time.objects.get(event_start_time=utc_dt)
    except Time.DoesNotExist:
        logger.debug("Time "+str(utc_dt)+" does not exist, creating...")
        time = Time.objects.create(event_start_time=utc_dt)

    time_pref = TimePreference(event=event,
                               time=time,
                               user=curr_user,
                               created_ts=datetime.now())

    try:
        time_pref.save()
    except Exception as err:
        #TODO: catch specific errors
        resp['error_code'] = -1
        resp['msg'] = "Error saving time preference "+str(start_ts)+" to event "+str(event.id)+", error: "+str(err)
    else:
        logger.debug("Succesfully added time preference "+str(start_ts)+" to event "+str(event.id))
        resp['error_code'] = 0
        resp['msg'] = "Succesfully added time preference "+str(start_ts)+" to event "+str(event.id)

    return resp

@transaction.atomic
def add_not_installed_users_to_db(not_installed_phone_nos, event):
    """
        Function to atomically add not installed users to DB
    """
    try:
        for no in not_installed_phone_nos:
            not_installed_user =  User()
            not_installed_user.phone_no = no
            not_installed_user.save()
            event.participants.add(not_installed_user)
    except IntegrityError, err:
        raise IntegrityError(err)

def add_participants(event=None, participants=[], owner=None):
    """
        Function to add participants to an event
    """

    try:
        #Get the list of phone numbers in order to query the
        #user DB
        phone_list = []
        for guy in participants:
            phone_list.append(guy['phone'])
        users_in_db = User.objects.filter(phone_no__in=phone_list)
        logger.debug("Users in db: "+str(users_in_db))
    except Exception, e:
        raise NoUsersInDB(e)
    
    #Now add the users in phone_list to the list of participants.
    #XXX Handle case where this user is not yet in DB.
    #   - If a user is not yet in DB, a new user would be 
    #   created for the phone_no not in the DB.
    #   - When this new user logs in, his details will be updated
    #   in the DB, and he would automatically see the events,
    #   since he has already been added as a participant to the event
    for user in users_in_db:
        event.participants.add(user)

    #Finally add the owner himself as a participant
    if owner:
        event.participants.add(owner)

    #For participants not in the installed base, store them
    #in a separate table
    installed_phone_nos = [user.phone_no for user in users_in_db]
    logger.debug("Installed phone_nos "+str(installed_phone_nos))
    not_installed_phone_nos = [x for x in phone_list if x not in installed_phone_nos]
    logger.debug("Not installed phone_nos "+str(not_installed_phone_nos))
    
    try:
        add_not_installed_users_to_db(not_installed_phone_nos, event)
    except IntegrityError, err:
        raise IntegrityError(err)

    logger.debug("Saving uninstalled phone nos: "+str(not_installed_phone_nos))


def update_event_add_participants(event, payload, curr_user):
    """
        Method to update participants for an event
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    """
    resp = {}
    try:
        #Add participants to the event
        add_participants(event=event, 
                         participants=payload, 
                         owner=None)
    except NoUsersInDB as err:
        logger.error("Exception while looking for users: "+str(participants)+ 
                        "in db during create event: "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Exception while looking for users: "+str(participants)+\
                        "in db during update event, add participants: "+str(err)
        return resp
    except IntegrityError as err:
        logger.error("Integrity error while adding not installed users in DB: "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Integrity error while adding not installed users in DB: "+str(err)
        return resp

    logger.debug("List of phone nos added to the event: "+str(payload))
    resp['error_code'] = 0
    resp['msg'] = "List of phone nos added to the event: "+str(payload)

    return resp

def update_event_like_location(event, payload, curr_user):
    """
        Method to update like location preference
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response

    """
    resp = {}
    try:
        location_pref_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    #Get the location preference from DB
    try:
        loc_pref = LocationPreference.objects.get(id=location_pref_id)
    except LocationPreference.DoesNotExist as err:
        logger.error("Location preference "+str(location_pref_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "Location preference "+str(location_pref_id)+\
                    " does not exist in the database"
        return resp
    try:
        loc_like = LocationLike(user=curr_user,
                                location_pref=loc_pref,
                                created_ts=datetime.now(),
                                event=event)
        loc_like.save()
    except Exception as err:
        logger.error("Unable to save location like in DB "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Unable to save location like in DB "+str(err)
        return resp

    #data to be sent back
    resp['error_code'] = 0
    resp['msg'] = "Location preference liked succesfully"

    return resp

def update_event_like_time(event, payload, curr_user):
    """
        Method to update like time preference
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    """
    resp = {}
    try:
        time_pref_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] ="Missing field in the payload, "+str(err)
        return resp
    
    #Get the time preference from DB
    try:
        time_pref = TimePreference.objects.get(id=time_pref_id)
    except TimePreference.DoesNotExist as err:
        logger.error("Time preference "+str(time_pref_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "Time preference "+str(time_pref_id)+\
                    " does not exist in the database"
        return resp

    try:
        time_like = TimeLike(user=curr_user,
                            time_pref=time_pref,
                            created_ts=datetime.now(),
                            event=event)
        time_like.save()
    except Exception as err:
        logger.error("Unable to save time like in DB "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Unable to save time like in DB "+str(err)
        return resp
    
    resp['error_code'] = 0
    resp['msg'] = "Time preference liked succesfully"

    return resp

def update_event_lock_time(event, payload, curr_user):
    """
        Method to lock event time
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    
    """
    resp = {}
    #Only owner can lock an event for now
    if event.owner != curr_user:
        resp['error_code'] = -1
        resp['msg'] = "Only owner can lock an event"
        return resp
    #If  event already has locked time pref send back error
    if event.locked_time_pref_id:
        logger.error("Event already has locked time preference, "+str(event.locked_time_pref_id))
        resp['error_code'] = -1
        resp['msg'] = "Event already has locked time preference, "+str(event.locked_time_pref_id)
        return resp

    try:
        time_pref_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    #Get the time preference from DB
    try:
        time_pref = TimePreference.objects.get(id=time_pref_id)
    except TimePreference.DoesNotExist as err:
        logger.error("Time preference "+str(time_pref_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "Time preference "+str(time_pref_id)+\
                    " does not exist in the database"
        return resp

    time_pref.locked = True
    time_pref.save()
    #Set the locked time_preference id in the event
    event.locked_time_pref_id = time_pref.id

    #Check if locked location is set and mark event as confirmed
    if event.locked_location_pref_id:
        event.status = 'confirmed'

    event.save()
    
    resp['error_code'] = 0
    resp['msg'] = "Time preference locked succesfully"

    return resp

def update_event_unlock_time(event, payload, curr_user):
    """
        Method to lock event time
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    
    """
    resp = {}
    #Only owner can unlock an event for now
    if event.owner != curr_user:
        resp['error_code'] = -1
        resp['msg'] = "Only owner can unlock an event"
        return resp
    #If  event does not already has locked time pref send back error
    if not event.locked_time_pref_id:
        logger.error("Event does not have a locked time preference")
        resp['error_code'] = -1
        resp['msg'] = "Event does not have a locked time preference"
        return resp

    try:
        time_pref_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    #Get the time preference from DB
    try:
        time_pref = TimePreference.objects.get(id=time_pref_id)
    except TimePreference.DoesNotExist as err:
        logger.error("Time preference "+str(time_pref_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "Time preference "+str(time_pref_id)+\
                    " does not exist in the database"
        return resp

    time_pref.locked = False
    time_pref.save()

    #Mark event status as unconfirmed
    event.status = 'unconfirmed'

    #Set the locked time_preference id in the event
    event.locked_time_pref_id = None


    event.save()
    
    resp['error_code'] = 0
    resp['msg'] = "Time preference unlocked succesfully"

    return resp

def update_event_lock_location(event, payload, curr_user):
    """
        Method to lock event location
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    
    """
    resp = {}
    #Only owner can lock an event for now
    if event.owner != curr_user:
        resp['error_code'] = -1
        resp['msg'] = "Only owner can lock an event"
        return resp

    #If  event already has locked time pref send back error
    if event.locked_location_pref_id:
        logger.error("Event already has locked location preference, "+str(event.locked_location_pref_id))
        resp['error_code'] = -1
        resp['msg'] = "Event already has locked location preference, "+str(event.locked_location_pref_id)
        return resp

    try:
        location_pref_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    #Get the time preference from DB
    try:
        location_pref = LocationPreference.objects.get(id=location_pref_id)
    except TimePreference.DoesNotExist as err:
        logger.error("Location preference "+str(location_pref_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "Location preference "+str(location_pref_id)+\
                    " does not exist in the database"
        return resp

    location_pref.locked = True
    location_pref.save()
    #Set the locked location_preference id in the event
    event.locked_location_pref_id = location_pref.id
    
    #Check if locked time is set and mark event as confirmed
    if event.locked_time_pref_id:
        event.status = 'confirmed'

    event.save()
    resp['error_code'] = 0
    resp['msg'] = "Location preference locked succesfully"

    return resp

def update_event_unlock_location(event, payload, curr_user):
    """
        Method to lock event time
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    
    """
    resp = {}
    #Only owner can unlock an event for now
    if event.owner != curr_user:
        resp['error_code'] = -1
        resp['msg'] = "Only owner can unlock an event"
        return resp
    #If  event does not already has locked time pref send back error
    if not event.locked_location_pref_id:
        logger.error("Event does not have a locked location preference")
        resp['error_code'] = -1
        resp['msg'] = "Event does not have a locked location preference"
        return resp

    try:
        loc_pref_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp
    
    #Get the time preference from DB
    try:
        loc_pref = LocationPreference.objects.get(id=loc_pref_id)
    except LocationPreference.DoesNotExist as err:
        logger.error("Location preference "+str(loc_pref_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "Location preference "+str(loc_pref_id)+\
                    " does not exist in the database"
        return resp

    loc_pref.locked = False
    loc_pref.save()

    #Mark event status as unconfirmed
    event.status = 'unconfirmed'

    #Set the locked location_preference id in the event
    event.locked_location_pref_id = None


    event.save()
    
    resp['error_code'] = 0
    resp['msg'] = "Location preference unlocked succesfully"

    return resp

def update_event_remove_participant(event, payload, curr_user):
    """
        Method to remove participant from an event. Only
        the owner of the event can remove a participant
        Returns:
        
        resp {
                'error_code': 0/-1,
                'msg' : 
            }

        The caller needs to handle the response
    """
    
    resp = {}
    #Only owner can lock an event for now
    if event.owner != curr_user:
        resp['error_code'] = -1
        resp['msg'] = "Only owner can remove a participant"
        return resp

    try:
        participant_id = payload['id']
    except KeyError as err:
        logger.error("Missing field in the payload, "+str(err))
        resp['error_code'] = -1
        resp['msg'] = "Missing field in the payload, "+str(err)
        return resp

    #Get the participant from the DB
    try:
        user = User.objects.get(id=participant_id)
    except User.DoesNotExist as err:
        logger.error("User with id "+str(participant_id)+\
                    " does not exist in the database")
        resp['error_code'] = -1
        resp['msg'] = "User with id "+str(participant_id)+\
                    " does not exist in the database"
        return resp

    #Now remove the user from the event
    try:
        event.participants.remove(user)
    except Exception as err:
        logger.error("Unable to remove user "+str(participant_id)+" from event "+str(event.name))
        resp['error_code'] = -1
        resp['msg'] = "Unable to remove user "+str(participant_id)+" from event "+str(event.name)
        return resp
    
    event.save()
    logger.debug("Succesfully removed user :"+str(participant_id)+" from the event "+str(event.name))
    
    resp['error_code'] = 0
    resp['msg'] = "Succesfully removed user from the event"

    return resp

def build_event_details(event):
    """
        Method to build event details response dict 
        and return it back to the called.
    """
    res = {}
    if event:
        res['id'] = event.id
        res['name'] = event.name
        res['status'] = event.status
        res['is_mute'] = event.muted
        res['created_ts'] = calendar.timegm(event.created_ts.timetuple())
        res['owner'] = { 'name': event.owner.name,
                         'phone' : event.owner.phone_no
                       }
        res['latest_activity'] = event.latest_activity
    res_participants = []
    for participant in event.participants.all():
        res_participants.append({ 
                                'name': participant.name,
                                'user_id' : participant.user_id,
                                'id' : participant.id,
                                'phone' : participant.phone_no
                                })

    res['participants'] = res_participants

    #Get the location preferences for this event
    loc_prefs = LocationPreference.objects.filter(event=event) 
    #Get the time preferences for this event
    time_prefs = TimePreference.objects.filter(event=event)

    #XXX: This might be a bit inefficient with multiple DB queries
    #being made. Revisit this
    where = []
    for loc_pref in loc_prefs:
        #For each location preference get all the location likes
        loc_likes = LocationLike.objects.filter(location_pref=loc_pref)
        users = []
        users_liked_count = 0
        for like in loc_likes:
            users.append({
                            'name' : like.user.name,
                            'user_id' : like.user.user_id,
                            'phone' : like.user.phone_no
                         }
                        )
            users_liked_count += 1
        where.append( {
                        'location_id': loc_pref.id,
                        'place_id' : loc_pref.location.place_id,
                        'name' : loc_pref.location.name,
                        'address' : loc_pref.location.address,
                        'service' : loc_pref.location.service,
                        'lat' : loc_pref.location.latitude,
                        'lng' : loc_pref.location.longitude,
                        'phone_no' : loc_pref.location.phone_no,
                        'rating' : loc_pref.location.rating,  
                        'count_likes' : users_liked_count,
                        'users_liked' : users,
                        'locked' : loc_pref.locked
                      }
                    )
    #XXX Same here. check is this is too inefficient
    when = []
    for time_pref in time_prefs:
        #For each time preference get all the time likes
        time_likes = TimeLike.objects.filter(time_pref=time_pref)
        users = []
        users_liked_count = 0
        for like in time_likes:
            users.append({
                            'name' : like.user.name,
                            'user_id' : like.user.user_id,
                            'phone' : like.user.phone_no
                         }
                        )
            users_liked_count += 1
        when.append( {
                        'time_id': time_pref.id,
                        'start_ts' : calendar.timegm(time_pref.time.event_start_time.timetuple()),
                        'count_likes' : users_liked_count,
                        'users_liked' : users,
                        'locked' : time_pref.locked
                      }
                    )
    
    res['where'] = where
    res['when'] = when
    logger.debug("Returning event details for id: "+str(event.id)+" , "+str(res))
    return res
