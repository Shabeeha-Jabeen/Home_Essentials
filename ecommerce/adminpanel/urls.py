from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
 
    # Main Category Management
    path('categories/', views.category_management, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('categories/toggle/<int:pk>/', views.toggle_category_status, name='toggle_category_status'),

    # Sub Category
    path('subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('subcategories/edit/<int:pk>/', views.edit_subcategory, name='edit_subcategory'),
    path('subcategories/delete/<int:pk>/', views.delete_subcategory, name='delete_subcategory'),

    # Nested Category
    path('nested-categories/add/', views.add_nested_category, name='add_nested_category'),
    path('nested-categories/edit/<int:pk>/', views.edit_nested_category, name='edit_nested_category'),
    path('nested-categories/delete/<int:pk>/', views.delete_nested_category, name='delete_nested_category'),


    path('list/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/update/<int:pk>/', views.update_product, name='update_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('product/toggle/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),


    path('admin/banners/', views.banner_list, name='banner_list'),

# Carousel CRUD
    path('admin/carousel/add/', views.add_carousel, name='add_carousel'),
    path('admin/carousel/edit/<int:pk>/', views.edit_carousel, name='edit_carousel'),
    path('admin/carousel/delete/<int:pk>/', views.delete_carousel, name='delete_carousel'),

# Offer CRUD
    path('admin/offer/add/', views.add_offer, name='add_offer'),
    path('admin/offer/edit/<int:pk>/', views.edit_offer, name='edit_offer'),
    path('admin/offer/delete/<int:pk>/', views.delete_offer, name='delete_offer'),

    path('users/', views.user_list, name='user_list'),
    path('users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),


    path('brands/', views.brand_list, name='brand_list'),
    path('brands/delete/<int:brand_id>/', views.delete_brand, name='delete_brand'),

    path('wishlists/', views.admin_wishlist_view, name='admin_wishlist_list'),
    

    path('orders/', views.admin_order_list, name='admin_orders'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    
    path('reviews/', views.admin_reviews, name='admin_reviews'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),


    path('materials/add/', views.add_material, name='add_material'),
    path('materials/update/<int:pk>/', views.update_material, name='update_material'),
    path('materials/delete/<int:pk>/', views.delete_material, name='delete_material'),
    path('materials/list/', views.material_list, name='material_list'),


    path('admin/orders/', views.admin_order_list, name='admin_orders'),
    path('admin/order/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/order-item/approve/<int:item_id>/', views.approve_item_return, name='approve_item_return'),
    path('admin/cancel-item/<int:item_id>/', views.cancel_item_admin, name='cancel_item_admin'),
]
