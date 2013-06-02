from django.http import Http404
from django.shortcuts import render_to_response

def home(request, *args):
    return render_to_response('home.html', {})

