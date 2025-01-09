from django.urls import path
from .views import CarSearchView, UserRegistrationView, UserLoginView

urlpatterns = [
    path('api/car-search/', CarSearchView.as_view(), name='car-search'),
    path('api/user-registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('api/user-login/', UserLoginView.as_view(), name='user-login'),
]
