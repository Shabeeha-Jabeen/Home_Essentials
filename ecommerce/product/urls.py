from django.urls import path
from .views import (
    home, offers, product_list_view, product_search_view, 
    product_detail, wishlist_view, add_to_wishlist, 
    move_to_cart, wishlist_to_checkout,remove_from_wishlist,add_review
)

urlpatterns = [
    path('', home, name='home'),
    path('offers/', offers, name='offers'),
    path('products/', product_list_view, name='category_product_list'),
    path('search/', product_search_view, name='product_search'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('wishlist/', wishlist_view, name='wishlist_view'),
    path('add-to-wishlist/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist-to-checkout/<int:product_id>/', wishlist_to_checkout, name='wishlist_to_checkout'),
    path('remove/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('move-to-cart/<int:item_id>/', move_to_cart, name='move_to_cart'),
    path('add-review/<int:product_id>/', add_review, name='add_review'),
]