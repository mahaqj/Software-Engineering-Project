from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RestaurantManagerSignupForm, WarehouseManagerSignupForm, ItemForm, BatchForm
from . import services
from .decorators import warehouse_manager_required, restaurant_manager_required
from .models import SystemSettings, Item, Order
from django.contrib import messages
from django.http import HttpResponseServerError

####################################################### ACCOUNTS #######################################################

class CustomLoginView(LoginView):
    template_name = "warehouse_inventory/login.html"

    def form_valid(self, form):
        try:
            user = form.get_user() #override form_valid to check the status before logging in
            if user.role == "restaurant manager": #check if they are approved
                restaurant_manager = services.get_restaurant_manager(user)
                if restaurant_manager and restaurant_manager.status != "approved":
                    return redirect("login") #redirect back to login if not approved
            login(self.request, user)
            return redirect(self.get_redirect_url())
        except Exception:
            return HttpResponseServerError("An error occurred during login. Please try again later.")
        
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
    try:
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
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, "warehouse_inventory/warehouse_signup.html", {"form": form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def warehouse_home_view(request):
    try:
        return render(request, "warehouse_inventory/warehouse_home.html")
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def restaurant_manager_requests_view(request):
    try:
        pending_requests = services.get_pending_restaurant_manager_requests()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/restaurant_manager_requests.html", {"pending_requests": pending_requests})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def process_request(request, user_id, action):  #user_id as parameter from url, action options are approve and reject
    try:
        services.process_restaurant_manager_request(user_id, action)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect("restaurant_manager_requests")

################################################## RESTAURANT MANAGER ##################################################

def restaurant_manager_signup(request):
    try:
        if request.method == "POST": #if form submitted
            form = RestaurantManagerSignupForm(request.POST)
            if form.is_valid():
                user_data = form.cleaned_data
                services.create_restaurant_manager(user_data)
                return redirect("login")
        else:
            form = RestaurantManagerSignupForm()
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, "warehouse_inventory/signup.html", {"form": form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def restaurant_home_view(request):
    try:
        manager = services.get_restaurant_manager(request.user)
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/restaurant_home.html", {"manager": manager})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def view_restaurant_manager(request, user_id):
    try:
        manager = services.get_restaurant_manager_by_id(user_id)
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/view_restaurant_manager.html", {"manager": manager})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def edit_restaurant_manager(request, user_id):
    try:
        manager = services.get_restaurant_manager_by_id(user_id)
        if request.method == "POST":
            services.edit_restaurant_manager(manager, request.POST)
            return redirect("view_restaurant_manager", user_id)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, "warehouse_inventory/edit_restaurant_manager.html", {"manager": manager})

################################################### FOOD MANAGEMENT ####################################################

@login_required
@warehouse_manager_required
def view_food_items(request):
    try:
        items = services.get_all_food_items()
        items_with_stock = [{"item": item, "stock": services.get_current_stock(item.item_id)} for item in items]
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/view_food_items.html", {"items_with_stock": items_with_stock})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def add_food_item(request):
    try:
        if request.method == "POST":
            item_form = ItemForm(request.POST, request.FILES)
            batch_form = BatchForm(request.POST)
            if item_form.is_valid() and batch_form.is_valid():
                item = services.add_food_item(item_form, batch_form)
                if item:
                    return redirect("view_food_items")
        else:
            item_form = ItemForm()
            batch_form = BatchForm()
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, "warehouse_inventory/add_food_item.html", {"item_form": item_form, "batch_form": batch_form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def delete_food_item(request, item_id): #item_id as parameter from url
    try:
        if request.method == "POST":
            services.delete_food_item(item_id)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect("view_food_items")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def delete_batch(request, batch_id):
    try:
        if request.method == "POST":
            services.delete_batch_by_id(batch_id)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect("expired_food_items")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required #services?
def update_price_list(request):
    try:
        items = services.get_all_food_items()
        if request.method == "POST":
            for item in items:
                new_price = request.POST.get(f"price_{item.item_id}") #get da val
                if float(new_price) != 0.0:
                    services.update_item_price(item.item_id, new_price)
                    return redirect("view_food_items")
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, "warehouse_inventory/update_price_list.html", {"items": items})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def expired_food_items(request):
    try:
        expired_batches = services.get_expired_batches()
        expiring_soon_batches = services.get_expiring_soon_batches()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/expired_food_items.html", {"expired_batches": expired_batches, "expiring_soon_batches": expiring_soon_batches})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def restock_items(request):
    try:
        low_stock_items = services.get_low_stock_items_with_stock()
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, "warehouse_inventory/restock_items.html", {"low_stock_items": low_stock_items})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def restock_item(request, item_id):
    try:
        if request.method == "POST":
            quantity = request.POST.get("quantity")
            expiry_date = request.POST.get("expiry_date")
            if quantity and expiry_date:
                services.restock_item(item_id, int(quantity), expiry_date)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect("restock_items")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def update_fees(request):
    try:
        settings = SystemSettings.objects.first() #fetch singleton
        if not settings:
            return render(request, 'warehouse_inventory/update_fees.html', {'error': 'System settings are missing.'})
        if request.method == 'POST':
            urgent_delivery_fee = request.POST.get('urgent_delivery_fee')
            late_payment_fee = request.POST.get('late_payment_fee')
            services.update_fees_in_system(settings, urgent_delivery_fee, late_payment_fee)
            return redirect('update_fees')
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, 'warehouse_inventory/update_fees.html', {'settings': settings})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def view_product_catalog(request):
    try:
        items = services.get_all_food_items()
        items_with_stock = [{"item": item, "stock": services.get_current_stock(item.item_id)} for item in items]
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/product_catalog.html", {"items_with_stock": items_with_stock})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def add_to_cart(request, item_id):
    try:
        if request.method == "POST":
            quantity_requested = int(request.POST.get("quantity", 0))
            item = get_object_or_404(Item, pk=item_id)
            order = services.get_current_order_for_user(request.user)
            success, msg = services.add_item_to_order(order, item, quantity_requested)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")        
    return redirect('product_catalog')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def view_cart(request):
    try:
        manager = request.user.restaurantmanager
        urgent_delivery_fee = services.get_urgent_delivery_fee()
        order, created = services.get_or_create_processing_order(manager)
        order_items = services.get_order_items(order)
        total_amount = services.calculate_total_amount(order_items)
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/view_cart.html", {"order": order, "order_items": order_items, "total_amount": total_amount, "urgent_delivery_fee": urgent_delivery_fee})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def place_order(request):
    try:
        manager = request.user.restaurantmanager
        order = get_object_or_404(Order, restaurant_manager=manager, status="processing")
        total = services.calculate_order_total(order)
        services.create_or_update_payment(order, total)
        order.status = "placed"
        order.save()
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect('view_orders')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def view_orders(request):
    try:
        manager = request.user.restaurantmanager
        orders = services.get_orders_for_manager(manager)
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/view_orders.html", orders)

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def warehouse_orders(request):
    try:
        orders = services.get_placed_orders_for_warehouse()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/warehouse_orders.html', {'orders': orders})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def fulfill_order(request, order_id):
    try:
        services.fulfill_order_by_id(order_id)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect('warehouse_orders')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def reject_order(request, order_id):
    try:
        if request.method == "POST":
            services.reject_order_and_restore_stock(order_id)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect('warehouse_orders')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def cancel_order(request, order_id):
    try:
        services.cancel_order_and_restore_stock(order_id)
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return redirect('view_orders')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def restaurant_manager_billing(request):
    try:
        manager = request.user.restaurantmanager
        pending_payments = services.get_pending_bills(manager)
        total_due = sum([payment.amount for payment in pending_payments])
        if request.method == 'POST':
            services.mark_payments_as_paid(manager)
            return redirect('restaurant_manager_billing')
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/restaurant_manager_billing.html', {'pending_payments': pending_payments, 'total_due': total_due})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def view_payments(request):
    try:
        payments = services.get_all_payments()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, "warehouse_inventory/view_payments.html", {"payments": payments})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def warehouse_monthly_earnings(request):
    try:
        monthly_earnings = services.get_monthly_earnings_for_current_year()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/monthly_earnings.html', {'monthly_earnings': monthly_earnings})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def overall_report(request):
    try:
        most_ordered = services.get_most_ordered_item()
        total_items = services.get_total_items()
        total_revenue = services.get_total_revenue()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/overall_report.html', {'most_ordered': most_ordered, 'total_items': total_items, 'total_revenue': total_revenue,})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def approved_restaurant_managers(request):
    try:
        approved_managers = services.get_approved_restaurant_managers()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/approved_restaurant_managers.html', {'approved_managers': approved_managers})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def send_notification(request, restaurant_manager_id):
    try:
        restaurant_manager = services.get_restaurant_manager_by_id(restaurant_manager_id)
        warehouse_manager = services.get_warehouse_manager_instance()
        
        if request.method == 'POST':
            content = request.POST.get('message_content')
            if content:
                services.create_message(warehouse_manager, restaurant_manager, content)
                return redirect('approved_restaurant_managers')
            else:
                messages.error(request, "Message content cannot be empty.")
    except Exception as e:
        return HttpResponseServerError("An internal server error occurred. Please try again later")
    return render(request, 'warehouse_inventory/send_notification.html', {'restaurant_manager': restaurant_manager})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def restaurant_manager_notifications(request):
    try:
        restaurant_manager = services.get_restaurant_manager_by_user(request.user)
        notifications = services.get_notifications_for_manager(restaurant_manager)
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/restaurant_manager_notifications.html', {'notifications': notifications})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def warehouse_home(request):
    try:
        low_stock_count = services.count_low_stock_items()
    except Exception as e:
        return HttpResponseServerError("An error occurred while fetching data. Please try again later.")
    return render(request, 'warehouse_inventory/warehouse_home.html', {'low_stock_count': low_stock_count})

#----------------------------------------------------------------------------------------------------------------------#