#services.py for keeping views.py clean, making testing easier, and making code reusable
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from .models import RestaurantManager, Item, WarehouseManager

####################################################### ACCOUNTS #######################################################

def create_warehouse_manager(user_data):
    if WarehouseManager.objects.exists():
        return None #maintain singleton
    User = get_user_model()
    user = User.objects.create_user(username=user_data["username"], email=user_data["email"], password=user_data["password"], manager_name=user_data["manager_name"], contact_no=user_data["contact_no"], location=user_data["location"], role="warehouse manager",)
    warehouse_manager = WarehouseManager.objects.create(user=user)
    return warehouse_manager
    
def create_restaurant_manager(user_data):
    User = get_user_model()
    user = User.objects.create_user(username=user_data["username"], email=user_data["email"], password=user_data["password"], manager_name=user_data["manager_name"], contact_no=user_data["contact_no"], location=user_data["location"], role="restaurant manager",)
    restaurant_manager = RestaurantManager.objects.create(user=user, restaurant_name=user_data["restaurant_name"], bank_acc_no=user_data["bank_acc_no"], status="pending",)
    return restaurant_manager 

################################################## WAREHOUSE MANAGER ###################################################

def get_pending_restaurant_manager_requests():
    return RestaurantManager.objects.filter(status="pending")

def process_restaurant_manager_request(user_id, action):
    manager = get_object_or_404(RestaurantManager, pk=user_id)
    if action == "approve":
        manager.status = "approved"
    elif action == "reject":
        manager.status = "rejected"
    manager.save()

################################################## RESTAURANT MANAGER ##################################################

def get_restaurant_manager(user):
    return RestaurantManager.objects.filter(pk=user.user_id).first()

def get_restaurant_manager_by_id(user_id):
    return get_object_or_404(RestaurantManager, pk=user_id)

def edit_restaurant_manager(manager, data):
    manager.user.manager_name = data.get("manager_namee")
    manager.user.contact_no = data.get("contact_no")
    manager.bank_acc_no = data.get("bank_acc_no")
    manager.user.save()
    manager.save()

################################################### FOOD MANAGEMENT ####################################################

def get_all_food_items():
    return Item.objects.all()

def add_food_item(form):
    if form.is_valid():
        form.save()
        return True
    return False

def delete_food_item(item_id):
    item = get_object_or_404(Item, pk=item_id)
    item.delete()

def edit_food_item_price(item, new_price):
    item.unit_price = float(new_price)
    item.save()

def get_expired_food_items():
    return Item.objects.filter(expiry_date__lt=now().date())

########################################################################################################################