from django.shortcuts import render #renders html templates
from django.shortcuts import redirect #redirects users
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RestaurantManagerSignupForm
 
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
