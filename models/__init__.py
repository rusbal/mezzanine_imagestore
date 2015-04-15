#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'
from imagestore.utils import load_class, get_model_string
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from imagestore.models.album import Album
from imagestore.models.image import Image


class AlbumImage(models.Model):
    album = models.ForeignKey(Album)
    image = models.ForeignKey(Image)
    order = models.IntegerField(_('Order'), default=0)

    __original_order = None

    def __init__(self, *args, **kwargs):
        super(AlbumImage, self).__init__(*args, **kwargs)
        self.__original_order = self.order

    def __unicode__(self):
        return "%s" % self.pk

    class Meta:
        db_table = 'imagestore_album_images'
        ordering = ('order',)
        unique_together = ('album', 'image')
        app_label = 'imagestore'

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = 0
        super(AlbumImage, self).save(*args, **kwargs)
        if self.order != self.__original_order:
            """
            When order is changed, set Albums head image to the first in order
            """
            first_img = AlbumImage.objects.filter(album = self.album).all()[0]
            self.album.set_head(self.album.pk, first_img.image)
        self.__original_order = self.order


# Album = load_class(getattr(settings, 'IMAGESTORE_ALBUM_MODEL', 'imagestore.models.album.Album'))
# Image = load_class(getattr(settings, 'IMAGESTORE_IMAGE_MODEL', 'imagestore.models.image.Image'))

# This labels and classnames used to generate permissons labels
image_applabel = Image._meta.app_label
image_classname = Image.__name__.lower()

album_applabel = Album._meta.app_label
album_classname = Album.__name__.lower()

albumimage_applabel = AlbumImage._meta.app_label
albumimage_classname = AlbumImage.__name__.lower()


from upload import AlbumUpload
