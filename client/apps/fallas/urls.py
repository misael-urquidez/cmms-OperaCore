from django.urls import path

from . import views

app_name = "fallas"

urlpatterns = [
    path("", views.ListaReportesView.as_view(), name="index"),
    path("reporte/", views.ReporteFallaView.as_view(), name="reporte"),
    path("lista/", views.ListaReportesView.as_view(), name="lista"),
]
