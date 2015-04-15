#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'

try:
    from django.conf.urls import include, patterns, url
except ImportError:
    from django.conf.urls.defaults import include, patterns, url

from imagestore.views import AlbumListView

urlpatterns = patterns('',
    url(r'^', include('imagestore.urls', namespace='imagestore')),
    )
