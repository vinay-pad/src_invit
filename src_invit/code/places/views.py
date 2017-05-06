import os
import logging
import json
import requests

# Get an instance of a logger
logger = logging.getLogger(__name__)
from code.user.models import User
from code.user.views import is_user_logged_in
from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from code.utils.generic_utils import set_return_response

GOOGLE_PLACES_KEY = str(os.environ.get('GOOGLE_PLACES_KEY'))
GOOGLE_PLACES_AUTOCOMPLETE_URL = 'https://maps.googleapis.com/maps/api/place/photo'

class PlacesView(View):
    """
        View module for the places API. We will currently be
        using the Google places API. This might be subject to 
        change in the future.
        For now there is no iOS places API available, it is only
        available for android. So we will be using the places
        web service API to make the request from the app go through
        our server and serve back the results from the places API.
    """
    
    action = 'suggest'
    res = {
            'status' : 'success',
            'error_code' : 0,
            'error_msg': '',
            'data': ''
    }
    
    #Auto complete radius for google places API.
    autocomplete_radius = 10000

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(PlacesView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
            All post requests come through this method.
            The response is Json
        """
        user_id = None
        logger.debug("Inside generic post dispatch method for places api with action "+str(self.action))
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
    
    def suggest_places(self, request, user_id):
        """
            Method that uses the google places query autocomplete
            API https://maps.googleapis.com/maps/api/place/queryautocomplete/output?parameters
            'params' sent by the client will be the substring the user types and also the
            lat/long of the user 
        """

        try:
            query = request.POST['query']
            latitude = request.POST['latitude']
            longitude =  request.POST['longitude'] 
        except KeyError as err:
            logger.error("Post params missing key, "+str(err))
            set_return_response(self.res, "failed", -1, 
                            "Post params missing key, "+str(err))
            return self.res
        
        logger.debug("Got suggest places api request with query: "+str(query)+
                     " latitude: "+str(latitude)+" longitude: "+str(longitude))
        
        #Make the call to the google places web service api, specifically
        #use the 'queryautocomplete' endpoint.
        payload = {
                    'key':  GOOGLE_PLACES_KEY,
                    'photoreference': "CnRnAAAA-vVzmC1jz6JWlFlnNVjn3KVpiUGmJqIkpLXizGqHhp4mWZfUAlpkP9yCg3QfZ5BV4ZKL7i1JTMbRSk4qb78U-tVL2L5_4uD0uBn46UsXr    neHhbGul1f_Ez_joBn5C6VwaogNfPtGNjmR4qyQyevGRhIQ4YWa5_DPeq7fRM3pRh1V5xoUCbkHO_58CCHncVG78CKcnVpXvi4",
                    'maxwidth' : 200
                  }
        logger.debug("payload: "+str(payload))
        url = GOOGLE_PLACES_AUTOCOMPLETE_URL
        r = requests.get(url, params=payload)
        logger.debug("Got response to autocomplete request: "+r.text)
        data = {}
        set_return_response(self.res, "success", 0, 
                            "Succesfully retrieved places suggestions", data)
        return self.res
        
    #Map of method names
    method_map = {
        'suggest' : suggest_places,
    }
