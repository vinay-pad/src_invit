
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

from django.db import models
from code.user.models import User


#Class to capture the location at which an event is happening
#or might be happening if it is a preference.
class Location(models.Model):
    place_id = models.TextField()
    name = models.TextField()
    address = models.TextField()
    latitude = models.DecimalField(max_digits=12, decimal_places=9, blank=True, null=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=9, blank=True, null=True)
    service = models.TextField()
    phone_no = models.TextField(null=True)
    rating = models.TextField(null=True)
    
    class Meta:
        """
            The combination of 'place_id' and 'service' should 
            be unique for a given location
        """
        unique_together = ("place_id", "service")

class Time(models.Model):
    event_start_time = models.DateTimeField()
    event_end_time = models.DateTimeField(null=True)

# For now i think it makes more sense
# to have a separate class for pending
# and confirmed events. Especially for something
# like 'unconfirm' action where we might have to
# go back to an pending version of an event.
#
class Event(models.Model):
    name = models.TextField()
    status = models.CharField(max_length=11)
    muted = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='owner')
    created_ts = models.DateTimeField()
    participants = models.ManyToManyField(User, related_name='participant')
    #Specifying a through relationship between location_pref and 
    #location since some of the preference details itself need 
    #to be captured like, 
    #   - when the preference was added
    #   - who added the preference
    #   etc
    location_preference = models.ManyToManyField(Location, 
                            through = 'LocationPreference',
                            through_fields = ('event','location'))
    time_preference = models.ManyToManyField(Time, 
                            through = 'TimePreference',
                            through_fields = ('event', 'time'))

    #id of the locked location preference
    locked_location_pref_id = models.BigIntegerField(null=True)
    #id of the locked time preference
    locked_time_pref_id = models.BigIntegerField(null=True)
    #Latest activity on the event
    #XXX: For now this is just a text field set in the backend
    latest_activity = models.TextField()

    def delete(self, *args, **kwargs):
        logger.debug("Event "+str(self.name)+" with id: "+str(self.id)+" is being deleted")
        #TODO: Do we need to keep track of deleted events? May be Trash vs delete permanently?
        #XXX: For now just deleting
        super(Event, self).delete(*args, **kwargs) # Call the "real" save() method.

#Through class for location preferences added by a user for an event
class LocationPreference(models.Model):
    event = models.ForeignKey(Event)
    location = models.ForeignKey(Location)
    user = models.ForeignKey(User)
    created_ts = models.DateTimeField()
    locked = models.BooleanField(default=False)

#Through class for time preferences added by a user for an event
class TimePreference(models.Model):
    event = models.ForeignKey(Event)
    time = models.ForeignKey(Time)
    user = models.ForeignKey(User)
    created_ts = models.DateTimeField()
    locked = models.BooleanField(default=False)

class LocationLike(models.Model):
    """
        model that captures likes for location preference
    """
    user = models.ForeignKey(User)
    location_pref = models.ForeignKey(LocationPreference)
    created_ts = models.DateTimeField()
    event = models.ForeignKey(Event) 
    class Meta:
        """
            User can like a given loc_pref only once
        """
        unique_together = ("user", "location_pref")

class TimeLike(models.Model):
    """
        model that captures likes for time preference
    """
    user = models.ForeignKey(User)
    time_pref = models.ForeignKey(TimePreference)
    created_ts = models.DateTimeField()
    event = models.ForeignKey(Event) 
    class Meta:
        """
            User can like a given time_pref only once
        """
        unique_together = ("user", "time_pref")
