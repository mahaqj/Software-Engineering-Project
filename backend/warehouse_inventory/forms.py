from django import forms
from .models import User, RestaurantManager, WarehouseManager, Item, Batch

######################################################################################################################################################

class WarehouseManagerSignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['manager_name', 'username', 'email', 'password', 'contact_no', 'location']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "warehouse manager"
        user.set_password(self.cleaned_data['password']) #hash the password before saving
        if commit:
            user.save()
            warehouse_manager = WarehouseManager.objects.create(user=user)
            warehouse_manager.save()
        return user
    
######################################################################################################################################################

class RestaurantManagerSignupForm(forms.ModelForm):
    restaurant_name = forms.CharField(max_length=255)
    bank_acc_no = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ['manager_name', 'username', 'email', 'password', 'contact_no', 'location']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "restaurant manager"
        user.set_password(self.cleaned_data['password']) #hash the password before saving
        if commit:
            user.save()
            restaurant_manager = RestaurantManager.objects.create(user=user, restaurant_name=self.cleaned_data['restaurant_name'], bank_acc_no=self.cleaned_data['bank_acc_no'], status="pending")
            restaurant_manager.save()
        return user
    
######################################################################################################################################################

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["item_name", "category", "unit_price", "image"]

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get("unit_price")
        if unit_price is None or unit_price <= 0:
            raise forms.ValidationError("Unit price must be greater than 0.")
        return unit_price
 
######################################################################################################################################################
   
class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["quantity", "expiry_date"]
        widgets = {"expiry_date": forms.DateInput(attrs={"type": "date"}),} #calendar date picker

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is None or quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0.")
        return quantity

######################################################################################################################################################

# from django import forms
# from .models import Message

# class MessageForm(forms.ModelForm):
#     class Meta:
#         model = Message
#         fields = ['content']
#         widgets = {'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message...'})}