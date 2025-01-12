from django.contrib import admin
from .models import UserProfile, Feedback, CarSearch

admin.site.register(UserProfile)
admin.site.register(Feedback)
admin.site.register(CarSearch)