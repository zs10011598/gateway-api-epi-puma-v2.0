from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class Index(APIView):

	def get(self, request):
		"""
			Description: API root
		"""
		return Response({'message': 'Welcome API Epi-Puma v2.0!'}, status=status.HTTP_200_OK)