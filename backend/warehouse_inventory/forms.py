from django import forms
from .models import User, RestaurantManager

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
            restaurant_manager = RestaurantManager.objects.create(
                user=user,
                restaurant_name=self.cleaned_data['restaurant_name'],
                bank_acc_no=self.cleaned_data['bank_acc_no'],
                status="pending"
            )
            restaurant_manager.save()
        return user
    
######################################################################################################################################################
