from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import UserProfile, Feedback, CarSearch
from .serializers import CarSearchSerializer, UserProfileSerializer

class CarSearchView(APIView):
    def get(self, request):
        car_name = request.query_params.get('car_name', None)
        car_color = request.query_params.get('car_color', None)
        car_model = request.query_params.get('car_model', None)
        cars = CarSearch.objects.filter(car_name=car_name, car_color=car_color, car_model=car_model)
        serializer = CarSearchSerializer(cars, many=True)
        return Response(serializer.data)

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=201)
        return Response(serializer.errors, status=400)

class UserLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = UserProfile.objects.get(username=username, password=password)
            return Response({"message": "User logged in successfully!"}, status=200)
        except UserProfile.DoesNotExist:
            return Response({"message": "Invalid username or password!"}, status=400)

def shop_page(request):
    return render(request, 'shop.html', {'shop_name': 'Магазин автомобилей'})

def feedback_page(request):
    return render(request, 'feedback.html')

def contact_info_page(request):
    return render(request, 'contact_info.html')

def about_page(request):
    return render(request, 'about.html')

def send_feedback(request):
    if request.method == 'POST':
        feedback_text = request.POST.get('feedback')
        Feedback.objects.create(message=feedback_text)
        return HttpResponseRedirect('/feedback/')