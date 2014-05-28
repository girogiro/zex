from django.conf.urls import patterns, url

from zex import views

urlpatterns = patterns('',
#	url(r'^$', views.index, name='index'),
	url(r'^update$', views.update, name='update'),
	url(r'^(?P<datum_zasadnutia>[^/]+)?/?(?P<cislo_bodu>[^/]+)?/?$', views.index, name='index'),
)
