from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, restaurant_manager_signup, restaurant_home_view, warehouse_home_view
from .views import delete_food_item, edit_food_item, edit_restaurant_manager, view_restaurant_manager, expired_food_items
from .views import restaurant_manager_requests_view, process_request, add_food_item, view_food_items, warehouse_manager_signup

urlpatterns = [
    path("signup/", restaurant_manager_signup, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("restaurant_home/", restaurant_home_view, name="restaurant_home"),
    path("warehouse_home/", warehouse_home_view, name="warehouse_home"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("restaurant_manager_requests/", restaurant_manager_requests_view, name="restaurant_manager_requests"),
    path("process_request/<int:user_id>/<str:action>/", process_request, name="process_request"),
    path("add_food_item/", add_food_item, name="add_food_item"),
    path("view_food_items/", view_food_items, name="view_food_items"),
    path("delete_food_item/<int:item_id>/", delete_food_item, name="delete_food_item"),
    path("edit_food_item/<int:item_id>/", edit_food_item, name="edit_food_item"),
    path("edit_restaurant_manager/<int:user_id>/", edit_restaurant_manager, name="edit_restaurant_manager"),
    path("view_restaurant_manager/<int:user_id>/", view_restaurant_manager, name="view_restaurant_manager"),
    path("expired_food_items/", expired_food_items, name="expired_food_items"),
    path("warehouse_signup/", warehouse_manager_signup, name="warehouse_signup"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
