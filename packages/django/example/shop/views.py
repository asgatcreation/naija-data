from django.http import HttpResponse, JsonResponse
from rest_framework import generics

import naija_data as ng
from django_naija.choices import lga_choices

from .forms import CustomerForm
from .serializers import CustomerSerializer


def signup(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        return HttpResponse(f"Saved {customer.name}", status=201)
    return HttpResponse(form.as_div(), status=400 if request.method == "POST" else 200)


def lgas_for_state(request):
    """GET /lgas/?state=Lagos -> {"lgas": [["NG025001", "Agege"], ...]} for a dependent <select>."""
    state = ng.get_state(request.GET.get("state", ""))
    if state is None:
        return JsonResponse({"error": "Unknown state"}, status=404)
    return JsonResponse({"state": state.code, "lgas": lga_choices(state.code)})


class CustomerCreate(generics.CreateAPIView):
    serializer_class = CustomerSerializer
    authentication_classes: list = []
    permission_classes: list = []
