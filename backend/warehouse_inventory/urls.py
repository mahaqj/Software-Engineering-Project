from django.urls import path
from .views import restaurant_manager_signup, CustomLoginView, restaurant_home_view, warehouse_home_view
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("signup/", restaurant_manager_signup, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('restaurant_home/', restaurant_home_view, name='restaurant_home'),
    path('warehouse_home/', warehouse_home_view, name='warehouse_home'),
    path("logout/", LogoutView.as_view(), name="logout"),
]