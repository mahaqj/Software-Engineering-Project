from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

######################################################################################################################################################

# DISCLAIMER: do not remove the following comments yet
# class User(models.Model): #user model -> abstract base class
#     user_id = models.AutoField(primary_key=True) #auto-incrementing pk
#     manager_name = models.CharField(max_length=255)
#     username = models.CharField(max_length=150, unique=True)
#     email = models.EmailField(unique=True) #unique to prevent duplicate restaurants in the system, etc
#     password = models.CharField(max_length=255)
#     contact_no = models.CharField(max_length=20)
#     location = models.CharField(max_length=255)
#     role = models.CharField(max_length=20, choices=[("warehouse manager", "Warehouse Manager"), ("restaurant manager", "Restaurant Manager")]) #first value is stored in db, second is displayed

#     def __str__(self):
#         return self.manager_name #string rep of the object, improves readability (example below)
#         #print(user) -> output: Maha instead of print(user) -> output: <User: User object (1)> (not very useful)

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

    def __str__(self):
        return f"Warehouse Manager: {self.user.manager_name}"

######################################################################################################################################################
    
class RestaurantManager(models.Model): #extends user class
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) #if user is deleted, restaurantmanager is also deleted
    restaurant_name = models.CharField(max_length=255)
    bank_acc_no = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")])
    
    def __str__(self):
        return f"Restaurant Manager: {self.user.manager_name} for Restaurant {self.restaurant_name}"
    
######################################################################################################################################################

#not being used right now
class RequestToJoin(models.Model):
    request_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(RestaurantManager, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")])
    
    def __str__(self):
        return f"Request {self.request_id} = {self.status}"

######################################################################################################################################################

class Item(models.Model):
    item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    expiry_date = models.DateField()
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    
    def __str__(self):
        return f"Item name: {self.item_name}"

######################################################################################################################################################

class Order(models.Model): #placed by restaurant manager
    order_id = models.AutoField(primary_key=True)
    restaurant_manager = models.ForeignKey(RestaurantManager, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"Order {self.order_id} was placed by {self.restaurant_manager.restaurant_name}"

######################################################################################################################################################

class OrderItem(models.Model):
    sr_no = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.FloatField()

    def __str__(self):
        return f"Order {self.order.order_id} includes Item: {self.item.item_name}"

######################################################################################################################################################

class Payment(models.Model): #associated w order
    payment_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE) #each order has one payment
    amount = models.FloatField()
    due_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("paid", "Paid"), ("overdue", "Overdue")])

    def __str__(self):
        return f"Payment {self.payment_id} is {self.payment_status}"

######################################################################################################################################################