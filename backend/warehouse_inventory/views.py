from django.shortcuts import render #renders html templates
from django.shortcuts import redirect #redirects users
from django.contrib.auth import authenticate, login #django's built-in authentication funcs
from django.contrib import messages #allows us to send msgs to the frontend

# Create your views here.

# def login_view(request): #handles login logic
#     if request.method == 'POST': #if user submitted the login form
#         #now get info from from submission
#         email = request.POST['email']
#         password = request.POST['password']

#         #then authenticate the user