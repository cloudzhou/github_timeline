import json
from django.http import Http404
from django.shortcuts import render_to_response
from django.http.response import HttpResponse

def home(request, *args):
    return render_to_response('home.html', {})

def getjson(request, *args):
    resp = HttpResponse()
    js = {u'timeline': 
          {u'headline': u'Sh*t People Say', 
           u'text': u'People say stuff', 
           u'type': u'default', 
           u'date': [
                     {u'headline': u'Vine', 
                      u'startDate': u'2011,12,12', 
                      u'endDate': u'2012,1,27', 
                      u'asset': {
                                 u'media': u'https://vine.co/v/b55LOA1dgJU', 
                                 u'caption': u'', 
                                 u'credit': u''}, 
                      u'text': u'<p>Vine Test</p>'}
                     ], 
           u'startDate': u'2012,1,26'}}

    resp.write(json.dumps(js))
    return resp
