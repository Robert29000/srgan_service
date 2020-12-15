from django.db import models
from django.db.models import SET_NULL
from skimage import transform
import imageio
import numpy as np
from PIL import Image
# Create your models here.


class UploadedImage(models.Model):
    upload_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='uploaded_images/')

    def save(self, *args, **kwargs):
        super(UploadedImage, self).save(*args, **kwargs)
        img = imageio.imread(self.image.path, pilmode="RGB")
        if img.shape[0] != 128 or img.shape[1] != 128:
            img = transform.resize(img, (128, 128))
            img = (img * 255).astype(np.uint8)
            img = Image.fromarray(img)
            img.save(self.image.path)


class ResultImage(models.Model):
    result_id = models.AutoField(primary_key=True)
    related_image = models.ForeignKey(UploadedImage, to_field='upload_id', on_delete=SET_NULL, null=True)
    image = models.ImageField(upload_to='result_images/')