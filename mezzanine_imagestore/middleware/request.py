# coding: utf-8 
try:
    from threading import currentThread
except:
    # Django 1.2 and older
    from django.utils.thread_support import currentThread

_requests = {}

def get_request():
    return _requests[currentThread()]

class GlobalRequestMiddleware(object):
    def process_request(self, request):  
        _requests[currentThread()] = request
