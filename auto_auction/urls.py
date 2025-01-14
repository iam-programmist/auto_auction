from django.urls import path
from .views import * 

urlpatterns = [
    path('car-search/', CarSearchView.as_view(), name='car-search'),
    path('user-registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('user-login/', UserLoginView.as_view(), name='user-login'),
    path('shop/', shop_page, name='shop'),
    path('feedback/', feedback_page, name='feedback'),
    path('contact-info/', contact_info_page, name='contact_info'),
    path('about/', about_page, name='about'),
    path('send-feedback/', send_feedback, name='send_feedback'),
]
