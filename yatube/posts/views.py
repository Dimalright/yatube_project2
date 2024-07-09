from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


def index(request):
    return HttpResponse('Main page')


def group_posts(request, slug):
    try:
        int(slug)
        return HttpResponse('Ты указал номер группу')
    except ValueError:
        return HttpResponse('Любая дичь текстовая')