from rest_framework import serializers
from .models import CarSearch, UserProfile

class CarSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarSearch
        fields = ['user', 'car_name', 'car_color', 'car_model', 'search_date']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password', 'phone_number']
