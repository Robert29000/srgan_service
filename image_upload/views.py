# Create your views here.

from .models import UploadedImage, ResultImage
from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import urlencode
import keras
import imageio
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from .imagehelper import ImageHelper
from srgan_service.settings import BASE_DIR
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
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
    uploaded_object = UploadedImage.objects.get(upload_id=id_lr)
    img_lr = imageio.imread(uploaded_object.image.path)
    np_lr = ImageHelper.get_numpy_data(img_lr)

    np_hr = gen_model.predict(np_lr)
    np_hr = ImageHelper.denormalize(np_hr)

    image_hr = Image.fromarray(np_hr[0])
    image_hr = ImageHelper.get_image_file(image_hr)
    result_object = ResultImage(related_image=uploaded_object)
    result_object.save()
    image_name = "image_" + id_lr + ".png"
    result_object.image.save(image_name, InMemoryUploadedFile(
                        image_hr,       # file
                        None,               # field_name
                        image_name,           # file name
                        'image/png',       # content_type
                        image_hr.tell,  # size
                        None))
    result_object.save()
    response = HttpResponse(image_hr, content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="image.png"'
    return response


@api_view(('GET',))
def show_model_config_view(request):
    height = gen_model.input.shape[1]
    width = gen_model.input.shape[2]
    scale = gen_model.output.shape[1] / height
    response = {"Image heigth": height,
                "Image width": width,
                "Scale factor": scale}
    return Response(response)