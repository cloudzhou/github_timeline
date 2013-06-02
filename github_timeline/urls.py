from django.conf.urls import patterns, include, url

urlpatterns = patterns('github_timeline',

    url(r'^/?$', 'views.home'),
    url(r'^login/oauth/github/?$', 'views.login_github'),
    url(r'^getjson$', 'views.getjson', name='getjson'),

)
