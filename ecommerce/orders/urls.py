from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart, name='update_cart'),
    
    path('checkout/', views.checkout, name='checkout'),
    
    
  
    path('order-success/<int:order_id>/', views.order_success_view, name='order_success_view'),
    path('create-checkout-session/', views.create_checkout_session, name='create-checkout-session'),
    
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    
    
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.order_list, name='order_list'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('return/<int:order_id>/', views.return_order, name='return_order'),
]