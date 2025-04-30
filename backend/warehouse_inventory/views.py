from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RestaurantManagerSignupForm, WarehouseManagerSignupForm, ItemForm, BatchForm
from . import services
from .decorators import warehouse_manager_required, restaurant_manager_required
from .models import SystemSettings, Item, Order, OrderItem, Payment, RestaurantManager
from django.contrib import messages
from .services import add_item_to_order
from datetime import timedelta, date
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncMonth

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
    manager = services.get_restaurant_manager(request.user)
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
    items_with_stock = [{"item": item, "stock": services.get_current_stock(item.item_id)} for item in items]
    return render(request, "warehouse_inventory/view_food_items.html", {"items_with_stock": items_with_stock})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def add_food_item(request):
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
    return render(request, "warehouse_inventory/add_food_item.html", {"item_form": item_form, "batch_form": batch_form})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def delete_food_item(request, item_id): #item_id as parameter from url
    if request.method == "POST":
        services.delete_food_item(item_id)
    return redirect("view_food_items")

#----------------------------------------------------------------------------------------------------------------------#

def delete_batch(request, batch_id):
    if request.method == "POST":
        services.delete_batch_by_id(batch_id)
    return redirect("expired_food_items")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required #services?
def update_price_list(request):
    items = services.get_all_food_items()
    if request.method == "POST":
        for item in items:
            new_price = request.POST.get(f"price_{item.item_id}") #get da val
            if new_price:
                services.update_item_price(item.item_id, new_price)
        return redirect("view_food_items")
    return render(request, "warehouse_inventory/update_price_list.html", {"items": items})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def expired_food_items(request):
    expired_batches = services.get_expired_batches()
    expiring_soon_batches = services.get_expiring_soon_batches()
    return render(request, "warehouse_inventory/expired_food_items.html", {"expired_batches": expired_batches, "expiring_soon_batches": expiring_soon_batches})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def restock_items(request):
    low_stock_items = services.get_low_stock_items_with_stock()
    return render(request, "warehouse_inventory/restock_items.html", {"low_stock_items": low_stock_items})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def restock_item(request, item_id):
    if request.method == "POST":
        quantity = request.POST.get("quantity")
        expiry_date = request.POST.get("expiry_date")
        if quantity and expiry_date:
            services.restock_item(item_id, int(quantity), expiry_date)
    return redirect("restock_items")

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def update_fees(request):
    settings = SystemSettings.objects.first() #fetch singleton
    if not settings:
        return render(request, 'warehouse_inventory/update_fees.html', {'error': 'System settings are missing.'})
    if request.method == 'POST':
        urgent_delivery_fee = request.POST.get('urgent_delivery_fee')
        late_payment_fee = request.POST.get('late_payment_fee')
        services.update_fees_in_system(settings, urgent_delivery_fee, late_payment_fee)
        return redirect('update_fees')
    return render(request, 'warehouse_inventory/update_fees.html', {'settings': settings})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@restaurant_manager_required
def view_product_catalog(request):
    items = services.get_all_food_items()
    items_with_stock = [{"item": item, "stock": services.get_current_stock(item.item_id)} for item in items]
    return render(request, "warehouse_inventory/product_catalog.html", {"items_with_stock": items_with_stock})

#----------------------------------------------------------------------------------------------------------------------#

def add_to_cart(request, item_id):
    if request.method == "POST":
        quantity_requested = int(request.POST.get("quantity", 0))
        item = get_object_or_404(Item, pk=item_id)
        order = services.get_current_order_for_user(request.user)  # implement this
        success, msg = add_item_to_order(order, item, quantity_requested)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('product_catalog')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
def view_cart(request):
    manager = request.user.restaurantmanager
    system_settings = SystemSettings.objects.first()
    urgent_delivery_fee = system_settings.urgent_delivery_fee if system_settings else 0
    order, created = Order.objects.get_or_create(restaurant_manager=manager, status='processing')
    order_items = order.order_items.select_related('batch__item')
    total_amount = sum(item.quantity * item.unit_price for item in order_items)
    return render(request, "warehouse_inventory/view_cart.html", {"order": order, "order_items": order_items, "total_amount": total_amount, "urgent_delivery_fee": urgent_delivery_fee})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
def place_order(request):
    manager = request.user.restaurantmanager
    order = get_object_or_404(Order, restaurant_manager=manager, status="processing")
    total = 0
    for item in order.order_items.all():
        subtotal = item.quantity * item.unit_price
        total += subtotal
    if order.urgent_delivery:
        total += services.get_urgent_delivery_fee()
    payment, created = Payment.objects.get_or_create(
    order=order,
    defaults={'amount': total, 'due_date': timezone.now().date() + timedelta(days=7), 'payment_status': 'pending'})
    if not created:
        payment.amount = total
        payment.due_date = timezone.now().date() + timedelta(days=7)
        payment.payment_status = "pending"
        payment.save()
    order.status = "placed"
    order.save()
    return redirect('view_orders')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
def view_orders(request):
    manager = request.user.restaurantmanager
    processing_orders = Order.objects.filter(restaurant_manager=manager, status="processing")
    placed_orders = Order.objects.filter(restaurant_manager=manager, status="placed")
    fulfilled_orders = Order.objects.filter(restaurant_manager=manager, status="fulfilled")
    rejected_orders = Order.objects.filter(status='rejected')
    canceled_orders = Order.objects.filter(status='canceled')
    return render(request, "warehouse_inventory/view_orders.html", {"processing_orders": processing_orders, "placed_orders": placed_orders, "fulfilled_orders": fulfilled_orders, "rejected_orders": rejected_orders, "canceled_orders": canceled_orders})

#----------------------------------------------------------------------------------------------------------------------#

def warehouse_orders(request):
    orders = Order.objects.filter(status='placed').prefetch_related('order_items__batch__item')
    return render(request, 'warehouse_inventory/warehouse_orders.html', {'orders': orders})

#----------------------------------------------------------------------------------------------------------------------#

def fulfill_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    order.status = 'fulfilled'
    order.save()
    return redirect('warehouse_orders')

#----------------------------------------------------------------------------------------------------------------------#

def reject_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == "POST":
        with transaction.atomic(): #ensures rollback on error
            order.status = 'rejected'
            order.save()

            for item in order.order_items.all():
                batch = item.batch
                batch.quantity += item.quantity
                batch.save()
        return redirect('warehouse_orders')

#----------------------------------------------------------------------------------------------------------------------#

def cancel_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if order.status == 'placed':
        order.status = 'canceled'
        order.save()
        for order_item in order.order_items.all(): #roll back items
            batch = order_item.batch
            batch.quantity += order_item.quantity
            batch.save()
        return redirect('view_orders')
    else:
        return redirect('view_orders')

#----------------------------------------------------------------------------------------------------------------------#

@login_required
def restaurant_manager_billing(request):
    manager = request.user.restaurantmanager
    pending_payments = Payment.objects.filter(order__restaurant_manager=manager, payment_status='pending', order__status='fulfilled')
    total_due = sum([payment.amount for payment in pending_payments])
    if request.method == 'POST': #pay whole bill: mark all as paid
        for payment in pending_payments:
            payment.payment_status = 'paid'
            payment.save()
        return redirect('restaurant_manager_billing')
    return render(request, 'warehouse_inventory/restaurant_manager_billing.html', {'pending_payments': pending_payments,'total_due': total_due,})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
@warehouse_manager_required
def view_payments(request):
    payments = Payment.objects.select_related("order__restaurant_manager").all()
    return render(request, "warehouse_inventory/view_payments.html", {"payments": payments})

#----------------------------------------------------------------------------------------------------------------------#

def warehouse_monthly_earnings(request):
    payments = Payment.objects.filter(payment_status='paid', order__status='fulfilled')
    current_year = date.today().year
    payments = payments.filter(order__date__year=current_year) #limit to current year
    monthly_earnings = (payments.annotate(month=TruncMonth('order__date')).values('month').annotate(total=Sum('amount')).order_by('month')) #group by month and sum
    return render(request, 'warehouse_inventory/monthly_earnings.html', {'monthly_earnings': monthly_earnings})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
def overall_report(request):
    most_ordered = (OrderItem.objects.values('batch__item__item_name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity').first()) #get most ordered item (by quantity)
    total_items = OrderItem.objects.aggregate(total=Sum('quantity'))['total'] or 0
    from .models import Payment #total revenue from paid payments
    total_revenue = Payment.objects.filter(payment_status='paid').aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'warehouse_inventory/overall_report.html', {'most_ordered': most_ordered, 'total_items': total_items, 'total_revenue': total_revenue,})

#----------------------------------------------------------------------------------------------------------------------#

@login_required
def approved_restaurant_managers(request):
    approved_managers = RestaurantManager.objects.filter(status='approved')
    return render(request, 'warehouse_inventory/approved_restaurant_managers.html', {'approved_managers': approved_managers})







from django.shortcuts import render, redirect
from .models import RestaurantManager, Message, WarehouseManager
from django.contrib.auth.decorators import login_required


from django.shortcuts import render, redirect, get_object_or_404
from .models import RestaurantManager, Message, WarehouseManager
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404

# @login_required
# def send_notification(request, restaurant_manager_id):
#     restaurant_manager = RestaurantManager.objects.get(pk=restaurant_manager_id)
#     warehouse_manager = WarehouseManager.get_instance()  # Assumes there's only one warehouse manager
    
#     if request.method == 'POST':
#         content = request.POST['content']
#         # Create the message
#         Message.objects.create(
#             sender=warehouse_manager,
#             receiver=restaurant_manager,
#             content=content,
#         )
#         return redirect('approved_restaurant_managers')  # Redirect to approved managers list
    
#     return render(request, 'send_notification.html', {'restaurant_manager': restaurant_manager})
@login_required
def send_notification(request, restaurant_manager_id):
    restaurant_manager = RestaurantManager.objects.get(pk=restaurant_manager_id)
    warehouse_manager = WarehouseManager.get_instance() 
    
    if request.method == 'POST':
        content = request.POST.get('message_content') 
        if content: 
            #message
            Message.objects.create(sender=warehouse_manager, receiver=restaurant_manager, content=content,)
            return redirect('approved_restaurant_managers')  # Redirect to approved managers list
        else:
            messages.error(request, "Message content cannot be empty.")
    
    return render(request, 'warehouse_inventory/send_notification.html', {'restaurant_manager': restaurant_manager})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Message
@login_required
def restaurant_manager_notifications(request):
    try:
        # Get the RestaurantManager associated with the logged-in user
        restaurant_manager = RestaurantManager.objects.get(user=request.user)

        # Get all messages for this restaurant manager
        notifications = Message.objects.filter(receiver=restaurant_manager)

        return render(request, 'warehouse_inventory/restaurant_manager_notifications.html', {'notifications': notifications})
    except RestaurantManager.DoesNotExist:
        # Handle the case where the user is not a restaurant manager (or other error)
        return redirect('error_page')  # Redirect to an error page if needed
