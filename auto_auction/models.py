from django.db import models

class UserProfile(models.Model):
    username = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

class Feedback(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class CarSearch(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    car_name = models.CharField(max_length=255)
    car_color = models.CharField(max_length=50)
    car_model = models.CharField(max_length=100)
    search_date = models.DateTimeField(auto_now_add=True)
