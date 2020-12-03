from django.urls import path

from .views import ImageView, show_high_res_view

urlpatterns = [
    path('upload/', ImageView.as_view(), name='upload_image'),
    path('result/', show_high_res_view, name='result_image')
]