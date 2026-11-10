from django.urls import path

from apps.web import views

urlpatterns = [
    path("", views.catalogo, name="web-catalogo"),
    path("herramientas/<int:pk>/", views.detalle, name="web-detalle"),
    path("mis-reservas/", views.mis_reservas, name="web-mis-reservas"),
    path("publicar/", views.publicar, name="web-publicar"),
    path("ingresar/", views.ingresar, name="web-ingresar"),
    path("registro/", views.registro, name="web-registro"),
]
