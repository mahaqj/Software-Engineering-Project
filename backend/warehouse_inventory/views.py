from django.shortcuts import render #renders html templates
from django.shortcuts import redirect #redirects users
from django.contrib.auth import login
from django.utils.timezone import now
from .models import RestaurantManager, Item
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RestaurantManagerSignupForm, ItemForm, WarehouseManagerSignupForm

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
    try:
        manager = RestaurantManager.objects.get(user=request.user)
        print(f"Manager found: {manager}")  # Debugging output
    except RestaurantManager.DoesNotExist:
        manager = None
        print("Manager data not found.")

    return render(request, "warehouse_inventory/restaurant_home.html", {"manager": manager})

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
def process_request(request, user_id, action): #user_id as parameter from url
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

def add_food_item(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES) #handle image uploads
        if form.is_valid():
            form.save()
            return redirect("view_food_items") #redirect after adding
    else:
        form = ItemForm()
    return render(request, "warehouse_inventory/add_food_item.html", {"form": form})

######################################################################################################################################################

def view_food_items(request):
    items = Item.objects.all()
    return render(request, "warehouse_inventory/view_food_items.html", {"items": items})

######################################################################################################################################################

def delete_food_item(request, item_id): #item_id as parameter from url
    if request.method == "POST":
        item = get_object_or_404(Item, pk=item_id)
        item.delete()
    return redirect("view_food_items")

######################################################################################################################################################

def edit_food_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == "POST":
        new_price = request.POST.get("unit_price")
        if new_price:
            item.unit_price = float(new_price)
            item.save()
            return redirect("view_food_items")
    return render(request, "warehouse_inventory/edit_food_item.html", {"item": item})

######################################################################################################################################################

@login_required
def view_restaurant_manager(request, user_id):
    manager = get_object_or_404(RestaurantManager, pk=user_id)
    return render(request, "warehouse_inventory/view_restaurant_manager.html", {"manager": manager})

######################################################################################################################################################

@login_required
def edit_restaurant_manager(request, user_id):
    manager = get_object_or_404(RestaurantManager, pk=user_id)
    if request.method == "POST":
        manager.user.manager_name = request.POST.get("manager_name")
        manager.user.contact_no = request.POST.get("contact_no")
        manager.bank_acc_no = request.POST.get("bank_acc_no")
        manager.user.save()
        manager.save()
        return redirect("restaurant_home")
    return render(request, "warehouse_inventory/edit_restaurant_manager.html", {"manager": manager})

######################################################################################################################################################

@login_required
def expired_food_items(request):
    expired_items = Item.objects.filter(expiry_date__lt=now().date())
    return render(request, "warehouse_inventory/expired_food_items.html", {"expired_items": expired_items})

######################################################################################################################################################

def warehouse_manager_signup(request):
    if request.method == "POST":
        form = WarehouseManagerSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = WarehouseManagerSignupForm()
    return render(request, "warehouse_inventory/warehouse_signup.html", {"form": form})

######################################################################################################################################################