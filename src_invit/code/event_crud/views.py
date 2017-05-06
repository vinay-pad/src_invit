
import os
import logging
import json
import calendar

# Get an instance of a logger
logger = logging.getLogger(__name__)
from code.user.models import User
from code.user.views import is_user_logged_in
from django.http import JsonResponse
import tweepy

from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from code.utils.generic_utils import set_return_response
from code.event_crud.models import Event, Location, \
                                    LocationPreference, Time, \
                                    TimePreference, LocationLike, \
                                    TimeLike
from code.event_crud.services import set_event_latest_activity, \
                                     update_event_add_location, \
                                     update_event_add_time, \
                                     update_event_add_participants, \
                                     update_event_like_location, \
                                     update_event_like_time, \
                                     update_event_lock_time, \
                                     update_event_unlock_time, \
                                     update_event_lock_location, \
                                     update_event_unlock_location, \
                                     add_participants, fetch_event, \
                                     update_event_remove_participant, \
                                     build_event_details
from django.views.generic import View
from code.event_crud.exceptions import NoUsersInDB, NoEventInDB

#Vinay TODO: Remove explicit checks for user logged in and 
# and make the check using a decorator which is cleaner

class EventView(View):
    
    #This gets overriden in urls.py
    action = 'get'
    res = {
            'status' : 'success',
            'error_code' : 0,
            'error_msg': '',
            'data': ''
    }


    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(EventView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
            All post requests come through this method.
            The response is Json
        """
        user_id = None
        logger.debug("Inside generic post dispatch method with action "+str(self.action))
        self.res = {
                'status' : 'success',
                'error_code' : 0,
                'error_msg': '',
                'data': ''
        }
        
        #All methods for this class require the user to be logged in.
        if 'access_token' in request.POST:
            user_id = is_user_logged_in(request.POST['access_token'])
            if user_id:
                return JsonResponse(
                        self.method_map[self.action](self, request, user_id),
                        *args,
                        **kwargs
                    )

                
        logger.error("Error: User not logged in.")
        set_return_response(self.res, "failure", -1, "User not logged in")
        return JsonResponse(
                self.res,
                *args,
                **kwargs
            )

    @csrf_exempt
    def create_event(self, request, user_id):
        """
            API to create an event. It takes in the name
            of the event as well as the current invitees
            to the event
        """
        owner = User.objects.get(user_id=user_id)
        try:
            event_name = request.POST['name']
            participants = json.loads(request.POST['participants'])
            logger.debug("got name: "+str(event_name)+" and list: "+str(participants))
        except KeyError as err:
            logger.error("KeyError during create event: "+str(err))
            set_return_response(self.res, "failed", -1, "Key Error: "+str(err))
            return self.res
        
        #Save this event in the DB
        event = Event()
        event.name = event_name
        event.status = "pending"
        event.muted = False
        event.created_ts = datetime.now()
        event.owner = owner

        #First save this event. After saving add the remainaing
        # ManyToMany related lists
        event.save()
       
        try:
            #Add participants to the event
            add_participants(event=event, 
                             participants=participants, 
                             owner=owner)
        except NoUsersInDB as err:
            logger.error("Exception while looking for users: "+str(participants)+ 
                            "in db during create event: "+str(err))
            set_return_response(self.res, "failed", -1, 
                            "Exception while looking for users in db during create event")
            return self.res

        logger.debug("Event succesfully saved. List of phone nos "
                    "to be added to the event: "+str(participants))
        #data to be returned
        data = {}
        data['id'] = event.id
        data['name'] = event.name
        data['status'] = "pending"
        data['is_mute'] = "false"
        data['owner'] = { 'name' : owner.name, 'phone': owner.phone_no }
        data['created_ts'] = calendar.timegm(event.created_ts.timetuple())
        data['where'] = []
        data['when'] = []
        set_return_response(self.res, "success", 0, 
                        "Succesfully created event", data)
        return self.res

    def update_event(self, request, user_id):
        """
        """
        data = {}
        update_methods = {
            'add_location' : update_event_add_location,
            'add_time' : update_event_add_time,
            'add_participant' : update_event_add_participants,
            'like_location' : update_event_like_location,
            'like_time' : update_event_like_time,
            'lock_time' : update_event_lock_time,
            'unlock_time' : update_event_unlock_time,
            'lock_location' : update_event_lock_location,
            'unlock_location' : update_event_unlock_location,
            'remove_participant' : update_event_remove_participant 
        }

        try:
            eventid = request.POST['eventid']
            action = request.POST['action']
            payload = json.loads(request.POST['payload'])
        except KeyError as err:
            logger.error("Post params missing key, "+str(err))
            set_return_response(self.res, "failed", -1, 
                            "Post params missing key, "+str(err))
            return self.res
        
        logger.debug("Inside update_event for event: "+str(eventid)+
                     " with action: "+str(action))

        event = None
        try:
            event = fetch_event(eventid)
        except NoEventInDB as err:
            #Event does not exist
            logger.error("Event "+str(eventid)+" does not exist\n")
            set_return_response(self.res, "failed", -1, 
                            "Event "+str(eventid)+" does not exist in the database")
            return self.res

        #Get the current user
        curr_user = User.objects.get(user_id=user_id)
        try:
            resp = update_methods[action](event, payload, curr_user)
        except KeyError as err:
            logger.error("Unsupported update event action: "+str(action))
            set_return_response(self.res, "failed", -1, 
                            "Unsupported update event action: "+str(action))
            return self.res
        
        #Update the latest activity on the event before sending success msg
        set_event_latest_activity(event, curr_user, action)
        event.save()
        data = build_event_details(event)
        if resp['error_code'] == 0:
            set_return_response(self.res, "success", 0, 
                            resp['msg'], data)
        else:
            set_return_response(self.res, "failed", -1, 
                            resp['msg'], data)

        return self.res
    
    def get_all_events(self, curr_user):
        """
            Method to return all events for this user.
        """
        res = { 'events' : [] }
        #Get all the events from the DB, ordered by the most recently created
        events = Event.objects.filter(participants=curr_user).order_by('-created_ts')
        #For each event construct the response
        for event in events:
            event_data = {}
            event_data['id'] = event.id
            event_data['name'] = event.name
            event_data['status'] = event.status
            event_data['is_mute'] = event.muted
            event_data['owner'] = { 'name' : event.owner.name,
                                    'phone' : event.owner.phone_no
                                  }
            event_data['created_ts'] = calendar.timegm(event.created_ts.timetuple())
            event_data['latest_activity'] = event.latest_activity
            if event.status == 'confirmed':
                #Get the locked time preference
                time_pref = TimePreference.objects.get(
                                                id=event.locked_time_pref_id)
                #Get the locked location preference
                loc_pref = LocationPreference.objects.get(
                                                id=event.locked_location_pref_id)
                if time_pref:
                    event_data['when'] = [{
                                            'start_ts' : calendar.timegm(time_pref.time.event_start_time.timetuple())
                                         }]
                #TODO: XXX this might be expensive. revisit
                if loc_pref:
                    event_data['where'] = [{
                                            'name' : loc_pref.location.name,
                                            'address' : loc_pref.location.address,
                                            'place_id' : loc_pref.location.place_id,
                                            'lat' : loc_pref.location.latitude,
                                            'lng' : loc_pref.location.longitude
                                          }]
            
            logger.debug("FETCHED event for user: "+str(curr_user.name)+",  events:"+str(event_data)) 
            res['events'].append(event_data)
        
        return res

    def get_event(self, eventid=None):
        """
            Method to return details about the event with
            id eventid
        """
        res = {}
        if not eventid:
            return None
        
        #Get the event from the DB
        try:
            event = Event.objects.get(id=eventid)
        except Event.DoesNotExist, err:
            raise NoEventInDB(err)
            
        res = build_event_details(event)
        return res

    def get_events(self, request, user_id):
        """
            Method that is used to get all or one of the
            requested events
            Currently does not have support to return a subset
            of events, since we don't have such a use case yet.
        """
        #TODO: Add support to get a subset of events
        try:
            eventid = request.POST['eventid']
        except KeyError as err:
            logger.error("Post params missing key, "+str(err))
            set_return_response(self.res, "failed", -1, 
                            "Post params missing key, "+str(err))
            return self.res

        logger.debug("Got a get request for event id: "+str(eventid))
        
        curr_user = User.objects.get(user_id=user_id)
        if eventid == "all":
            data = self.get_all_events(curr_user);
        else:
            try:
                data = self.get_event(eventid=eventid)
            except NoEventInDB as err:
                #Event does not exist
                logger.error("Event "+str(eventid)+" does not exist\n")
                set_return_response(self.res, "failed", -1, 
                                "Event "+str(eventid)+" does not exist in the database")
                return self.res


        set_return_response(self.res, "success", 0, 
                            "Fetched event(s) succesfully", data)
        return self.res

    def delete_event(self, request, user_id):
        """
            API to delete an event.
            Only the owner of an event can delete an event
        """
        try:
            eventid = request.POST['eventid']
        except KeyError as err:
            logger.error("Post params missing key, "+str(err))
            set_return_response(self.res, "failed", -1, 
                            "Post params missing key, "+str(err))
            return self.res

        try:
            event = Event.objects.get(id=eventid)
        except Event.DoesNotExist, err:
            #Event does not exist
            logger.error("Event "+str(eventid)+" does not exist\n")
            set_return_response(self.res, "failed", -1, 
                            "Event "+str(eventid)+" does not exist in the database")
            return self.res
        
        #Check if the requesting user is owner of the event
        if str(user_id) != str(event.owner.user_id):
            logger.error("User: "+str(user_id)+" not authorized to delete event: "
                            +str(eventid)+":"+str(event.owner.user_id)+" \n")
            set_return_response(self.res, "failed", -1, 
                            "Not authorized to delete event: "+str(eventid)+" \n")
            return self.res
        
        #Delete the event from the database
        event.delete() 
        data = {'name': event.name}
        set_return_response(self.res, "success", 0, 
                            "Succesfully deleted event", data)
        return self.res
            
    #Map of method names
    method_map = {
        'create' : create_event,
        'update' : update_event,
        'get' : get_events,
        'delete': delete_event
    }
