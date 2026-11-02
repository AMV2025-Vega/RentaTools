from django.urls import path

from apps.publico.presentation.views import EstadisticasPublicasAPIView

urlpatterns = [path("publico/estadisticas/", EstadisticasPublicasAPIView.as_view(), name="publico-estadisticas")]
