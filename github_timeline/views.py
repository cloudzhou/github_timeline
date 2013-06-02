import base64, hashlib
import random, re, json, time
import httplib, urllib, hashlib
from datetime import datetime
from django.http import Http404
from django.db import IntegrityError
from django.shortcuts import render_to_response
from django.http.response import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, UserManager, check_password
from github_timeline.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET


def login_github(request):
    code = request.GET.get('code')
    if request.GET.get('code') is None:
        return HttpResponseRedirect('/login/oauth/github/')
    access_token = github_oauth_access_token(code)
    if access_token == '':
        return HttpResponseRedirect('/login/oauth/github/')
    (username, email) = get_github_user_meta(access_token)
    if username is None:
        return HttpResponseRedirect('/login/oauth/github/')
    github_authenticate(request, username, email)
    return HttpResponseRedirect('/')

def github_oauth_access_token(code):
    githup_connection = None
    try:
        githup_connection = httplib.HTTPSConnection('github.com', 443, timeout=10)
        params = urllib.urlencode({'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        githup_connection.request("POST", "/login/oauth/access_token", params, headers)
        response = githup_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            response = json.loads(json_str)
            access_token = str(response['access_token'])
            return access_token
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return ''

# https://api.github.com/user?access_token=17f605153e39f01f55062f2b4b719e9a14f1xxx
def get_github_user_meta(access_token):
    githup_connection = None
    try:
        githup_connection = httplib.HTTPSConnection('api.github.com', 443, timeout=10)
        headers = {"Host": "api.github.com", "Accept": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36"}
        githup_connection.request("GET", "/user?access_token=" + access_token, {}, headers)
        response = githup_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            response = json.loads(json_str)
            return (response['login'], response['email'])
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return None

def github_authenticate(request, username, email, password=None):
    user = None
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            print 'user IntegrityError'
    request.session.set_expiry(2592000)
    user.backend='django.contrib.auth.backends.ModelBackend'
    login(request, user)

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
