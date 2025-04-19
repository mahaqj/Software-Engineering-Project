from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, restaurant_manager_signup, restaurant_home_view, warehouse_home_view
from .views import delete_food_item, edit_restaurant_manager, view_restaurant_manager, expired_food_items
from .views import restaurant_manager_requests_view, process_request, add_food_item, view_food_items
from .views import update_fees, warehouse_manager_signup, update_price_list, restock_items, restock_item, delete_batch
from .views import view_product_catalog, add_to_cart, view_cart, place_order, view_orders, warehouse_orders
from .views import fulfill_order, reject_order, cancel_order, restaurant_manager_billing, view_payments

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
    path("edit_restaurant_manager/<int:user_id>/", edit_restaurant_manager, name="edit_restaurant_manager"),
    path("view_restaurant_manager/<int:user_id>/", view_restaurant_manager, name="view_restaurant_manager"),
    path("expired_food_items/", expired_food_items, name="expired_food_items"),
    path("warehouse_signup/", warehouse_manager_signup, name="warehouse_signup"),
    path("update_price_list/", update_price_list, name="update_price_list"),
    path("restock_items/", restock_items, name="restock_items"),
    path("restock_item/<int:item_id>/", restock_item, name="restock_item"),
    path("delete_batch/<int:batch_id>/", delete_batch, name="delete_batch"),
    path("update_fees/", update_fees, name="update_fees"),
    path("product_catalog/", view_product_catalog, name="product_catalog"),
    path("add-to-cart/<int:item_id>/", add_to_cart, name="add_to_cart"),
    path("cart/", view_cart, name="view_cart"),
    path("place_order/", place_order, name="place_order"),
    path("orders/", view_orders, name="view_orders"),
    path("warehouse-orders/", warehouse_orders, name="warehouse_orders"),
    path("warehouse-orders/fulfill/<int:order_id>/", fulfill_order, name="fulfill_order"),
    path("warehouse-orders/reject/<int:order_id>/", reject_order, name="reject_order"),
    path("orders/cancel/<int:order_id>/", cancel_order, name="cancel_order"),
    #path("send_message/<int:receiver_id>/", send_message, name="send_message"),
    #path('restaurant_manager_billing/', restaurant_manager_billing, name='restaurant_manager_billing'),
    path('billing/', restaurant_manager_billing, name='restaurant_manager_billing'),
    path("view_payments/", view_payments, name="view_payments"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
