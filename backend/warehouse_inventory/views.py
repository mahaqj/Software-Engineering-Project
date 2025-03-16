from django.shortcuts import render #renders html templates
from django.shortcuts import redirect #redirects users
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RestaurantManagerSignupForm
from .models import RestaurantManager
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import login

# Create your views here.

######################################################################################################################################################

def restaurant_manager_signup(request):
    if request.method == "POST": #if form submitted
        form = RestaurantManagerSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RestaurantManagerSignupForm()
    return render(request, "warehouse_inventory/signup.html", {"form": form})

######################################################################################################################################################

class CustomLoginView(LoginView):
    template_name = "warehouse_inventory/login.html"

    def form_valid(self, form):
        user = form.get_user() #override form_valid to check the status before logging in
        if user.role == "restaurant manager": #check if they are approved
            restaurant_manager = RestaurantManager.objects.filter(user=user).first()
            if restaurant_manager and restaurant_manager.status != "approved":
                return redirect("login") #redirect back to login if not approved
        login(self.request, user)
        return redirect(self.get_redirect_url())

    def get_redirect_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == "warehouse manager":
                return "/warehouse_home/"
            elif user.role == "restaurant manager":
                return "/restaurant_home/"
        return super().get_redirect_url()

######################################################################################################################################################

@login_required
def restaurant_home_view(request):
    return render(request, "warehouse_inventory/restaurant_home.html")

######################################################################################################################################################

@login_required
def warehouse_home_view(request):
    return render(request, "warehouse_inventory/warehouse_home.html")

######################################################################################################################################################

@login_required
def restaurant_manager_requests_view(request):
    if request.user.role != "warehouse manager":
        return redirect("warehouse_home") #iski zaroorat shayad nahi hai

    pending_requests = RestaurantManager.objects.filter(status="pending")
    return render(request, "warehouse_inventory/restaurant_manager_requests.html", {"pending_requests": pending_requests})

######################################################################################################################################################

@login_required
def process_request(request, user_id, action):
    if request.user.role != "warehouse manager":
        return HttpResponseForbidden("You do not have permission to perform this action.")

    restaurant_manager = get_object_or_404(RestaurantManager, user_id=user_id)

    if action == "approve":
        restaurant_manager.status = "approved"
    elif action == "reject":
        restaurant_manager.status = "rejected"
    
    restaurant_manager.save()
    return redirect("restaurant_manager_requests")

######################################################################################################################################################
