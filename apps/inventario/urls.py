from django.urls import path

from . import views

urlpatterns = [
    path('v1/refacciones/list/', views.ListRefaccionAPIView.as_view(), name='refaccion-list'),
    path('v1/refacciones/<int:pk>/', views.DetailRefaccionAPIView.as_view(), name='refaccion-detail'),
    path('v1/herramientas/list/', views.ListHerramientaAPIView.as_view(), name='herramienta-list'),
    path('v1/herramientas/<int:pk>/', views.DetailHerramientaAPIView.as_view(), name='herramienta-detail'),
    path('v2/movimientos/create/', views.CreateMovimientoAPIView.as_view(), name='movimiento-create'),
]
