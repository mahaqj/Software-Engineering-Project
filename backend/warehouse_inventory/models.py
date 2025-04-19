from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Create your models here.

######################################################################################################################################################

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    manager_name = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=[("warehouse manager", "Warehouse Manager"), ("restaurant manager", "Restaurant Manager")])

    REQUIRED_FIELDS = ["manager_name", "contact_no", "location", "role"]

    def __str__(self):
        return self.manager_name #string rep of the object, improves readability (example below)
        #print(user) -> output: Maha instead of print(user) -> output: <User: User object (1)> (not very useful)

######################################################################################################################################################

class WarehouseManager(models.Model): #extends user class
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) #if user is deleted, warehousemanager is also deleted

    def save(self, *args, **kwargs):
        if not self.pk and WarehouseManager.objects.exists():
            raise ValidationError("There can only be one Warehouse Manager.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Deleting the Warehouse Manager is not allowed.")

    @classmethod
    def get_instance(cls):
        instance, _ = cls.objects.get_or_create()
        return instance

    def __str__(self):
        return f"Warehouse Manager: {self.user.manager_name}"

######################################################################################################################################################
    
class RestaurantManager(models.Model): #extends user class
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) #if user is deleted, restaurantmanager is also deleted
    restaurant_name = models.CharField(max_length=255)
    bank_acc_no = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")])
    
    def __str__(self):
        return f"Restaurant Manager: {self.user.manager_name} - Restaurant {self.restaurant_name}"

######################################################################################################################################################

class SystemSettings(models.Model):
    urgent_delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_payment_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Urgent Delivery Fee: {self.urgent_delivery_fee}, Late Payment Fee: {self.late_payment_fee}"

######################################################################################################################################################

class Item(models.Model):
    item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    unit_price = models.FloatField()
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.item_name}"
    
######################################################################################################################################################
    
class Batch(models.Model):
    batch_id = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, related_name="batches", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    expiry_date = models.DateField()

    def __str__(self):
        return f"Batch {self.batch_id} - {self.item.item_name} - quantity: {self.quantity}"
    
######################################################################################################################################################

class Order(models.Model): #placed by restaurant manager
    order_id = models.AutoField(primary_key=True)
    restaurant_manager = models.ForeignKey(RestaurantManager, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[("cart", "In Cart"), ("placed", "Order Placed"), ("fulfilled", "Fulfilled"), ("rejected", "Rejected"), ("canceled", "Canceled")])
    urgent_delivery = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.order_id} by {self.restaurant_manager.restaurant_name} - {self.status}"

######################################################################################################################################################
 
class OrderItem(models.Model):
    sr_no = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE) #item of which batch
    quantity = models.IntegerField()
    unit_price = models.FloatField() #will come from the batch

    def __str__(self):
        return f"Order {self.order.order_id} - Batch {self.batch.batch_id} - {self.quantity} units"


######################################################################################################################################################

class Payment(models.Model): #associated w order
    payment_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE) #one order has one payment
    amount = models.FloatField() #total amount for the order
    due_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("paid", "Paid"), ("overdue", "Overdue")])

    def __str__(self):
        return f"Payment {self.payment_id} - {self.payment_status} for Order {self.order.order_id}"
    
######################################################################################################################################################
from django.utils import timezone

class Message(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(WarehouseManager, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(RestaurantManager, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    date_sent = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"From {self.sender.user.username} to {self.receiver.restaurant_name} on {self.date_sent}"