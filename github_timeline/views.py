# -*- coding: utf-8 -*-  
import base64, hashlib
import random, re, json, time
import httplib, urllib, hashlib
from datetime import datetime
from django.db import IntegrityError
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, UserManager, check_password
from github_timeline.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

def home(request, *args):
    return render_to_response('home.html',
                          {},
                          context_instance=RequestContext(request))

def getjson(request, *args):
    access_token = request.COOKIES.get('access_token') 
    if request.user.is_authenticated and access_token:
        js = demo_timeline()
        return HttpResponse(json.dumps(js), mimetype='application/json')
    else:
        js = unauth_user_timeline()
        return HttpResponse(json.dumps(js), mimetype='application/json')
    user_events = list_user_events(request, access_token)
    if user_events is None:
        js = unauth_user_timeline()
        return HttpResponse(json.dumps(js), mimetype='application/json')
    timeline_events = convert_to_timeline_events(user_events)
    return HttpResponse(json.dumps(timeline_events), mimetype='application/json')

def login_github(request):
    code = request.GET.get('code')
    if request.GET.get('code') is None:
        return HttpResponseRedirect('/')
    access_token = github_oauth_access_token(code)
    if access_token == '':
        return HttpResponseRedirect('/')
    (username, email) = get_github_user_meta(access_token)
    if username is None:
        return HttpResponseRedirect('/')
    github_authenticate(request, username, email, access_token)
    response = HttpResponseRedirect('/')
    response.set_cookie('access_token', access_token) 
    return response

def github_oauth_access_token(code):
    githup_connection = None
    try:
        githup_connection = httplib.HTTPSConnection('github.com', 443, timeout=10)
        params = urllib.urlencode({'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code})
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
        githup_connection.request('POST', '/login/oauth/access_token', params, headers)
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
        headers = {'Host': 'api.github.com', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'}
        githup_connection.request('GET', '/user?access_token=' + access_token, {}, headers)
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

def github_authenticate(request, username, email, access_token):
    user = None
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            user = User.objects.create_user(username, email, '123456')
        except IntegrityError:
            print 'user IntegrityError'
    request.session.set_expiry(2592000)
    user.backend='django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return user

def list_user_events(request, access_token):
    if not request.user.is_authenticated() or access_token is None:
        return None
    githup_connection = None
    try:
        githup_connection = httplib.HTTPSConnection('api.github.com', 443, timeout=10)
        headers = {'Host': 'api.github.com', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'}
        githup_connection.request('GET', '/users/' + request.user.username + '/events?access_token=' + access_token, {}, headers)
        response = githup_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            github_user_events = json.loads(json_str)
            return github_user_events
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return None

def convert_to_timeline_events(github_user_events):
    timeline_events = {}
    date = []
    last_startDate = '1970,1,1'
    for user_events in github_user_events:
        created_at = user_events['created_at']
        if user_events['type'] == 'PushEvent':
            for commit in user_events['payload']['commits']:
                author = commit['author']
                message = commit['message']
                timeline_event = {}
                timeline_event['headline'] = message
                timeline_event['text'] = '@' + author['name'] + ', ' + created_at
                timeline_event['startDate'] = created_at
                last_startDate = created_at
                date.append(timeline_event)
    timeline = {}
    timeline['headline'] = u'@' + author['name'] + u' GitHub 时间轴'
    timeline['text'] = u'展示您的 GitHub 历史'
    timeline['type'] = 'default'
    timeline['date'] = date
    timeline['startDate'] = last_startDate
    timeline_events['timeline'] = timeline
    return timeline_events
    
def unauth_user_timeline():
    js = {u'timeline': 
          {u'headline': u'GitHub 时间轴', 
           u'text': u'请先通过 GitHub 账户登录', 
           u'type': u'default', 
           u'date': [
                     {u'headline': u'hi，这是一个模拟的 commit 信息', 
                      u'startDate': u'2013-06-02T07:54:55Z', 
                      u'text': u'<p>哇！今天妹子真好看 ::>_<::</p>'}
                     ], 
           u'startDate': u'1970,1,1'}}
    return js

def demo_timeline():
    js = {"timeline": {"headline": u"@cloudzhou GitHub 时间轴", "text": u"展示您的 GitHub 历史", "startDate": "2013-06-02T05:45:37Z", "type": "default", "date": [{"headline": "github login", "text": "@cloudzhou, 2013-06-02T07:54:55Z", "startDate": "2013-06-02T07:54:55Z"}, {"headline": "github login", "text": "@cloudzhou, 2013-06-02T07:54:30Z", "startDate": "2013-06-02T07:54:30Z"}, {"headline": "Add: staticfiles", "text": "@U-SNDA\\zhangyang09, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "move README to root directory", "text": "@Michael Ding, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "Merge remote-tracking branch 'origin/master'", "text": "@Michael Ding, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "add login page", "text": "@Michael Ding, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "Add: some static files", "text": "@U-SNDA\\zhangyang09, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "merge github_user_oauth to master", "text": "@cloudzhou, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "Fix: emerge bugs", "text": "@U-SNDA\\zhangyang09, 2013-06-02T07:06:14Z", "startDate": "2013-06-02T07:06:14Z"}, {"headline": "via github login auth", "text": "@cloudzhou, 2013-06-02T06:54:10Z", "startDate": "2013-06-02T06:54:10Z"}, {"headline": "merge github_user_oauth to master", "text": "@cloudzhou, 2013-06-02T06:54:10Z", "startDate": "2013-06-02T06:54:10Z"}, {"headline": "init github timeline, including manage.py", "text": "@cloudzhou, 2013-06-02T05:50:14Z", "startDate": "2013-06-02T05:50:14Z"}, {"headline": "init github timeline", "text": "@cloudzhou, 2013-06-02T05:45:37Z", "startDate": "2013-06-02T05:45:37Z"}]}}
    return js
