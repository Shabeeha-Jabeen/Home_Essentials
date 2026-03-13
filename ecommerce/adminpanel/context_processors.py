from django.db.models import Q
from orders.models import Order

def new_orders_count(request):
    if request.user.is_authenticated and request.user.is_staff:

        count = Order.objects.filter(
            Q(status='Pending') | Q(status='Return Requested')
        ).count()
        return {'new_orders_count': count}
    
    return {'new_orders_count': 0}