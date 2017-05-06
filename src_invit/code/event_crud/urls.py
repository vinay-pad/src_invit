from django.conf.urls import patterns, url
from code.event_crud.views import EventView

urlpatterns = patterns('',
    url(r'^create', EventView.as_view(action="create")),
    url(r'^update', EventView.as_view(action="update")),
    url(r'^delete', EventView.as_view(action="delete")),
    url(r'^$', EventView.as_view(action="get")),
)
