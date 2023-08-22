import os
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class DataNodes(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
            Get data from graphql nodes
        """

        gateway_url = os.environ['GATURL']

        if 'query' in request.data.keys():
            query = request.data['query']
        else:
            return Response({"message": "`node` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

        body = {"query": query}

        try:
            return Response(requests.post(gateway_url, json=body).json(), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "error: {0}".format(str(e))}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
