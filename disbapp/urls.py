from django.urls import path
from . import views

urlpatterns = [
    path("", views.pagina_upload_view, name="form-nfe"),
    path("upload-xml-nfe/", views.upload_xml_nfe_view, name="upload-xml-nfe")
]
