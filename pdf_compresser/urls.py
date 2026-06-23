from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from compressor import views

urlpatterns = [
    path('', views.index, name='index'),
    path('compress/', views.compress_pdf, name='compress'),
    path('download/<str:filename>/', views.download_file, name='download'),
    path('progress/<str:job_id>/', views.compression_progress, name='progress'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
