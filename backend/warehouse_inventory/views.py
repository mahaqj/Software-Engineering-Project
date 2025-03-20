from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RestaurantManagerSignupForm, ItemForm, WarehouseManagerSignupForm
from .models import RestaurantManager, Item
from . import services
from .decorators import warehouse_manager_required, restaurant_manager_required

####################################################### ACCOUNTS #######################################################

class CustomLoginView(LoginView):
    template_name = "warehouse_inventory/login.html"

    def form_valid(self, form):
        user = form.get_user() #override form_valid to check the status before logging in
        if user.role == "restaurant manager": #check if they are approved
            restaurant_manager = services.get_restaurant_manager(user)
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

################################################## WAREHOUSE MANAGER ###################################################

def warehouse_manager_signup(request):
    form = WarehouseManagerSignupForm() #initialize form to avoid UnboundLocalError
    if request.method == "POST":
        form = WarehouseManagerSignupForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data #extract the data from the form
            warehouse_manager = services.create_warehouse_manager(user_data)
            if warehouse_manager:
                return redirect("login")
            else:
                form.add_error(None, "A Warehouse Manager already exists.")
        else:
            form = WarehouseManagerSignupForm()
    return render(request, "warehouse_inventory/warehouse_signup.html", {"form": form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def warehouse_home_view(request):
    return render(request, "warehouse_inventory/warehouse_home.html")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def restaurant_manager_requests_view(request):
    pending_requests = services.get_pending_restaurant_manager_requests()
    return render(request, "warehouse_inventory/restaurant_manager_requests.html", {"pending_requests": pending_requests})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def process_request(request, user_id, action):  #user_id as parameter from url, action options are approve and reject
    services.process_restaurant_manager_request(user_id, action)
    return redirect("restaurant_manager_requests")

################################################## RESTAURANT MANAGER ##################################################

def restaurant_manager_signup(request):
    if request.method == "POST": #if form submitted
        form = RestaurantManagerSignupForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data
            services.create_restaurant_manager(user_data)
            return redirect("login")
    else:
        form = RestaurantManagerSignupForm()
    return render(request, "warehouse_inventory/signup.html", {"form": form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def restaurant_home_view(request):
    manager = RestaurantManager.objects.filter(user=request.user).first()
    return render(request, "warehouse_inventory/restaurant_home.html", {"manager": manager})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def view_restaurant_manager(request, user_id):
    manager = services.get_restaurant_manager_by_id(user_id)
    return render(request, "warehouse_inventory/view_restaurant_manager.html", {"manager": manager})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def edit_restaurant_manager(request, user_id):
    manager = services.get_restaurant_manager_by_id(user_id)
    if request.method == "POST":
        services.edit_restaurant_manager(manager, request.POST)
        return redirect("view_restaurant_manager", user_id)
    return render(request, "warehouse_inventory/edit_restaurant_manager.html", {"manager": manager})

################################################### FOOD MANAGEMENT ####################################################

@login_required
@warehouse_manager_required
def view_food_items(request):
    items = services.get_all_food_items()
    return render(request, "warehouse_inventory/view_food_items.html", {"items": items})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def add_food_item(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES) #handle image uploads
        if services.add_food_item(form):
            return redirect("view_food_items")
    else:
        form = ItemForm()
    return render(request, "warehouse_inventory/add_food_item.html", {"form": form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def delete_food_item(request, item_id): #item_id as parameter from url
    if request.method == "POST":
        services.delete_food_item(item_id)
    return redirect("view_food_items")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def edit_food_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == "POST":
        new_price = request.POST.get("unit_price")
        if new_price:
            services.edit_food_item_price(item, new_price)
            return redirect("view_food_items")
    return render(request, "warehouse_inventory/edit_food_item.html", {"item": item})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def expired_food_items(request):
    expired_items = services.get_expired_food_items()
    return render(request, "warehouse_inventory/expired_food_items.html", {"expired_items": expired_items})

#----------------------------------------------------------------------------------------------------------------------#