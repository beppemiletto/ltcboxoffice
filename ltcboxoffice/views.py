from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    # return HttpResponse("<H1>My Home page</H1>")
    return render(request, 'home.html')
