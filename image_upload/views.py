# Create your views here.

from .models import UploadedImage, ResultImage
from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import urlencode
import keras
import imageio
import numpy as np
from numpy import array
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from srgan_service.settings import BASE_DIR
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from .serializers import ImageSerializer
import os

gen_model = keras.models.load_model(os.path.join(BASE_DIR, "generator_m_v2_1.h5"), compile=False)


class ImageView(APIView):
    def post(self, request, *args, **kwargs):
        image_serializer = ImageSerializer(data=request.data)
        if image_serializer.is_valid():
            obj = image_serializer.save()
            base_url = reverse('result_image')
            query_string = urlencode({'id': obj.upload_id})
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
        else:
            return HttpResponse(image_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)


def show_high_res_view(request):
    id_lr = request.GET.get('id')
    image_lr = UploadedImage.objects.get(upload_id=id_lr)
    img_path_lr = image_lr.image.path
    img_lr = imageio.imread(img_path_lr)
    list_lr = []
    list_lr.append(img_lr)
    np_lr = array(list_lr)
    np_lr = (np_lr.astype(np.float32) - 127.5)/127.5

    np_hr = gen_model.predict(np_lr)
    np_hr = ((np_hr + 1) * 127.5).astype(np.uint8)
    img_hr = Image.fromarray(np_hr[0])
    buffer = BytesIO()
    img_hr.save(fp=buffer, format="PNG")
    image_hr = ContentFile(buffer.getvalue())
    resImage = ResultImage()
    resImage.related_image_id = id_lr
    resImage.save()
    image_name = "image_" + id_lr +".png"
    resImage.image.save(image_name, InMemoryUploadedFile(
                        image_hr,       # file
                        None,               # field_name
                        image_name,           # file name
                        'image/png',       # content_type
                        img_hr.tell,  # size
                        None))
    resImage.save()
    response = HttpResponse(image_hr, content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="image.png"'
    return response
