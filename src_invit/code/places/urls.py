from django.conf.urls import patterns, url
from code.places.views import PlacesView

urlpatterns = patterns('',
    url(r'^suggest', PlacesView.as_view(action="suggest")),
)
