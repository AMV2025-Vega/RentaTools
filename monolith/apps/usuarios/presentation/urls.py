from django.urls import path

from apps.usuarios.presentation.views import LoginAPIView, LogoutAPIView, PerfilAPIView, RegistroAPIView

urlpatterns = [
    path("auth/registro/", RegistroAPIView.as_view(), name="auth-registro"),
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/yo/", PerfilAPIView.as_view(), name="auth-yo"),
]
