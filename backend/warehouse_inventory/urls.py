from django.urls import path
from .views import restaurant_manager_signup, CustomLoginView, restaurant_home_view, warehouse_home_view
from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import restaurant_manager_requests_view, process_request

urlpatterns = [
    path("signup/", restaurant_manager_signup, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('restaurant_home/', restaurant_home_view, name='restaurant_home'),
    path('warehouse_home/', warehouse_home_view, name='warehouse_home'),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("restaurant_manager_requests/", restaurant_manager_requests_view, name="restaurant_manager_requests"),
    path("process_request/<int:user_id>/<str:action>/", process_request, name="process_request"),
]