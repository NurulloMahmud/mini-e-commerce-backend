from django.urls import path
from .views import OrderView, OrderDetailView

urlpatterns = [
    path('', OrderView.as_view(), name='orders'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
]
