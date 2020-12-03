import numpy as np
from numpy import array
from django.core.files.base import ContentFile
from io import BytesIO

class ImageHelper(object):

    @staticmethod
    def normalize(data):
        return (data.astype(np.float32) - 127.5) / 127.5

    @staticmethod
    def denormalize(data):
        data = (data + 1) * 127.5
        return data.astype(np.uint8)

    @staticmethod
    def get_numpy_data(data):
        list = []
        list.append(data)
        np_data = array(list)
        np_data = ImageHelper.normalize(np_data)
        return np_data

    @staticmethod
    def get_image_file(image):
        buffer = BytesIO()
        image.save(fp=buffer, format="PNG")
        image_f = ContentFile(buffer.getvalue())
        return image_f