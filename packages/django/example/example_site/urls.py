from django.urls import path

from shop import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("lgas/", views.lgas_for_state, name="lgas"),  # for a dependent state -> LGA <select>
    path("api/customers/", views.CustomerCreate.as_view(), name="customer-create"),
]
