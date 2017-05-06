from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^user/',include('code.user.urls')),
    url(r'^events/',include('code.event_crud.urls')),
    url(r'^places/',include('code.places.urls')),
)
