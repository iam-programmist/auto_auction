from django.urls import path
from .views import CarSearchView, UserRegistrationView, UserLoginView

urlpatterns = [
    path('car-search/', CarSearchView.as_view(), name='car-search'),
    path('user-registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('user-login/', UserLoginView.as_view(), name='user-login'),
]
