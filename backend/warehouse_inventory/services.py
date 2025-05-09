#services.py for keeping views.py clean, making testing easier, and making code reusable
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from django.db.models import Sum, Value
from django.utils import timezone
from django.db import transaction
from django.db.models.functions import TruncMonth, Coalesce
from .models import RestaurantManager, Item, WarehouseManager, Batch, Order, OrderItem, SystemSettings, Payment, Message

####################################################### ACCOUNTS #######################################################

def create_warehouse_manager(user_data):
    if WarehouseManager.objects.exists():
        return None #maintain singleton
    User = get_user_model()
    user = User.objects.create_user(username=user_data["username"], email=user_data["email"], password=user_data["password"], manager_name=user_data["manager_name"], contact_no=user_data["contact_no"], location=user_data["location"], role="warehouse manager",)
    warehouse_manager = WarehouseManager.objects.create(user=user)
    SystemSettings.objects.get_or_create(defaults={"urgent_delivery_fee": 5.5, "late_payment_fee": 10})
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
    manager.user.manager_name = data.get("manager_name", manager.user.manager_name)
    manager.user.contact_no = data.get("contact_no", manager.user.contact_no)
    manager.bank_acc_no = data.get("bank_acc_no", manager.bank_acc_no)
    manager.user.save()
    manager.save()

################################################# INVENTORY MANAGEMENT #################################################

def get_all_food_items():
    return Item.objects.prefetch_related("batches").order_by("category", "item_name")

def add_food_item(item_form, batch_form):
    if item_form.is_valid() and batch_form.is_valid():
        item = item_form.save() #save item
        batch = batch_form.save(commit=False) #get batch instance
        batch.item = item
        batch.save()
        return item
    return None

def update_item_price(item_id, new_price):
    item = get_object_or_404(Item, pk=item_id)
    item.unit_price = float(new_price)
    item.save()

def delete_batch_by_id(batch_id): #deletes specific batch
    batch = get_object_or_404(Batch, pk=batch_id)
    batch.delete()

def delete_food_item(item_id): #deletes all batches of that item
    item = get_object_or_404(Item, pk=item_id)
    item.batches.all().delete()
    item.delete()

def get_expired_food_items():
    return Item.objects.filter(expiry_date__lt=now().date())

def get_expired_batches():
    return Batch.objects.filter(expiry_date__lt=now().date())

def get_expiring_soon_batches(days=7):
    today = date.today()
    upcoming_expiry = today + timedelta(days=days)
    return Batch.objects.filter(expiry_date__gte=today, expiry_date__lte=upcoming_expiry)

def get_current_stock(item_id):
    item = get_object_or_404(Item, pk=item_id)
    return item.batches.aggregate(total_stock=Sum("quantity"))["total_stock"] or 0 #sums up all item quantities across all batches

def restock_item(item_id, quantity, expiry_date):
    item = get_object_or_404(Item, pk=item_id)
    batch = Batch.objects.create(item=item, quantity=quantity, expiry_date=expiry_date)
    return batch

def get_low_stock_items(margin=10):
    return Item.objects.annotate(total_stock=Coalesce(Sum("batches__quantity"), Value(0))).filter(total_stock__lt=margin)

def count_low_stock_items(margin=10):
    count = get_low_stock_items(margin).count()
    print(f"Low stock count in services: {count}")
    return count

def get_low_stock_items_with_stock():
    low_stock_items = get_low_stock_items()
    return [{"item": item, "stock": get_current_stock(item.item_id)} for item in low_stock_items]

def update_fees_in_system(settings, urgent_delivery_fee, late_payment_fee):
    settings.urgent_delivery_fee = float(urgent_delivery_fee)
    settings.late_payment_fee = float(late_payment_fee)
    settings.save()

def get_current_order_for_user(user):
    return Order.objects.filter(restaurant_manager=user.restaurantmanager, status='processing').first() or Order.objects.create(restaurant_manager=user.restaurantmanager, status='processing')

def add_item_to_order(order, item, quantity_requested): #the most insane function
    remaining_quantity = quantity_requested
    used_batches = []
    batches = item.batches.filter(quantity__gt=0).order_by('expiry_date')
    for batch in batches:
        if remaining_quantity <= 0:
            break
        take_qty = min(batch.quantity, remaining_quantity)
        OrderItem.objects.create(order=order, batch=batch, quantity=take_qty,unit_price=item.unit_price)
        batch.quantity -= take_qty
        batch.save()
        used_batches.append((batch.batch_id, take_qty))
        remaining_quantity -= take_qty
    if remaining_quantity > 0:
        return False, f"Not enough stock to fulfill {quantity_requested} units of {item.item_name}."
    batch_info = ", ".join([f"Batch {b[0]} ({b[1]} units)" for b in used_batches])
    return True, f"Added {quantity_requested} x {item.item_name} to cart using: {batch_info}."

def calculate_total_amount(orders):
    total = 0
    for order in orders:
        order_total = 0
        for item in order.order_items.all():
            item_total = item.quantity * item.unit_price
            order_total += item_total
        total += order_total
    return total

def get_urgent_delivery_fee():
    settings = SystemSettings.objects.first()
    return float(settings.urgent_delivery_fee) if settings else 0

def calculate_order_total(order):
    total = sum(item.quantity * item.unit_price for item in order.order_items.all())
    if order.urgent_delivery:
        total += get_urgent_delivery_fee()
    return total

def create_or_update_payment(order, total):
    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={'amount': total, 'due_date': timezone.now().date() + timedelta(days=7), 'payment_status': 'pending'})
    if not created:
        payment.amount = total
        payment.due_date = timezone.now().date() + timedelta(days=7)
        payment.payment_status = "pending"
        payment.save()

def get_orders_for_manager(manager):
    return {"processing_orders": Order.objects.filter(restaurant_manager=manager, status="processing"), "placed_orders": Order.objects.filter(restaurant_manager=manager, status="placed"), "fulfilled_orders": Order.objects.filter(restaurant_manager=manager, status="fulfilled"), "rejected_orders": Order.objects.filter(status="rejected"), "canceled_orders": Order.objects.filter(status="canceled")}

def get_placed_orders_for_warehouse():
    return Order.objects.filter(status='placed').prefetch_related('order_items__batch__item')

def get_or_create_processing_order(manager):
    return Order.objects.get_or_create(restaurant_manager=manager, status='processing')

def get_order_items(order):
    return order.order_items.select_related('batch__item')

def calculate_total_amount(order_items):
    return sum(item.quantity * item.unit_price for item in order_items)

def fulfill_order_by_id(order_id):
    order = get_object_or_404(Order, order_id=order_id)
    order.status = 'fulfilled'
    order.save()
    return order

def reject_order_and_restore_stock(order_id):
    order = get_object_or_404(Order, order_id=order_id)
    with transaction.atomic():
        order.status = 'rejected'
        order.save()
        for item in order.order_items.select_related('batch').all():
            batch = item.batch
            batch.quantity += item.quantity
            batch.save()
    return order

def cancel_order_and_restore_stock(order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if order.status == 'placed':
        order.status = 'canceled'
        order.save()
        for item in order.order_items.all():
            batch = item.batch
            batch.quantity += item.quantity
            batch.save()
    return order

def get_pending_bills(manager):
    return Payment.objects.filter(order__restaurant_manager=manager, payment_status='pending', order__status='fulfilled')

def mark_payments_as_paid(manager):
    pending_payments = Payment.objects.filter(order__restaurant_manager=manager, payment_status='pending', order__status='fulfilled')
    total_due = sum([payment.amount for payment in pending_payments])
    for payment in pending_payments:
        payment.payment_status = 'paid'
        payment.save()
    return pending_payments, total_due

def get_all_payments():
    return Payment.objects.select_related("order__restaurant_manager").filter(order__status="fulfilled")

def get_monthly_earnings_for_current_year():
    current_year = date.today().year
    payments = Payment.objects.filter(payment_status='paid', order__status='fulfilled')
    payments = payments.filter(order__date__year=current_year) #limited to current year
    monthly_earnings = (payments.annotate(month=TruncMonth('order__date')).values('month').annotate(total=Sum('amount')).order_by('month')) #group by month and sum
    return monthly_earnings

def get_most_ordered_item():
    return (OrderItem.objects.filter(order__status='fulfilled').values('batch__item__item_name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity').first()) #get the most ordered item (by quantity)

def get_total_items():
    return OrderItem.objects.filter(order__status='fulfilled').aggregate(total=Sum('quantity'))['total'] or 0

def get_total_revenue():
    return Payment.objects.filter(payment_status='paid').aggregate(total=Sum('amount'))['total'] or 0

def get_approved_restaurant_managers():
    return RestaurantManager.objects.filter(status='approved')

def get_restaurant_manager_by_id(restaurant_manager_id):
    return RestaurantManager.objects.get(pk=restaurant_manager_id)

def get_warehouse_manager_instance():
    return WarehouseManager.get_instance()

def create_message(sender, receiver, content):
    return Message.objects.create(sender=sender, receiver=receiver, content=content)

def get_restaurant_manager_by_user(user):
    return RestaurantManager.objects.get(user=user)

def get_notifications_for_manager(manager):
    return Message.objects.filter(receiver=manager)
