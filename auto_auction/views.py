from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class CarSearchView(APIView):
    def get(self, request):
        return Response({"cars": ["car1", "car2"]}, status=status.HTTP_200_OK)
