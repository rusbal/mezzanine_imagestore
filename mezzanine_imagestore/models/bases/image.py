#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'


from django.db import models
from django.db.models import permalink
from sorl.thumbnail.helpers import ThumbnailError
from tagging.fields import TagField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from sorl.thumbnail import ImageField, get_thumbnail
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User

try:
    import Image as PILImage
except ImportError:
    from PIL import Image as PILImage

from imagestore.utils import get_file_path, get_model_string

SELF_MANAGE = getattr(settings, 'IMAGESTORE_SELF_MANAGE', True)


class BaseImage(models.Model):
    """
    Image may belong to one or more Albums (as long as Albums belong to same User)
    Image belongs to a User
    """
    class Meta(object):
        abstract = True
        ordering = ('title', 'id')
        permissions = (
            ('moderate_images', 'View, update and delete any image'),
        )

    title = models.CharField(_('Title'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)
    tags = TagField(_('Tags'), blank=True)
    image = ImageField(verbose_name = _('File'), upload_to=get_file_path)
    created = models.DateTimeField(_('Created'), auto_now_add=True, null=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True, null=True)
    user = models.ForeignKey(User, verbose_name=_('Owner'), related_name='images', blank=True, null=True)
    albums = models.ManyToManyField(get_model_string('Album'), through='AlbumImage', verbose_name=_('Album'), related_name='images')

    @permalink
    def get_absolute_url(self):
        return 'imagestore:image', (), {'pk': self.id}

    def __unicode__(self):
        return '%s' % self.title

    def admin_thumbnail_path(self):
        try:
            return get_thumbnail(self.image, '100x100', crop='center').url
        except IOError:
            logger.exception('IOError for image %s', self.image)
            return 'IOError'
        except ThumbnailError, ex:
            return 'ThumbnailError, %s' % ex.message
    admin_thumbnail_path.short_description = _('Thumbnail path')

    def admin_thumbnail(self):
        try:
            return '<img src="%s">' % get_thumbnail(self.image, '100x100', crop='center').url
        except IOError:
            logger.exception('IOError for image %s', self.image)
            return 'IOError'
        except ThumbnailError, ex:
            return 'ThumbnailError, %s' % ex.message

    admin_thumbnail.short_description = _('Thumbnail')
    admin_thumbnail.allow_tags = True


#noinspection PyUnusedLocal
def setup_imagestore_permissions(instance, created, **kwargs):
        if not created:
            return
        try:
            from imagestore.models import Album, Image
            album_type = ContentType.objects.get(
                #app_label=load_class('imagestore.models.Album')._meta.app_label,
                app_label = Album._meta.app_label,
                name='Album'
            )
            image_type = ContentType.objects.get(
                #app_label=load_class('imagestore.models.Image')._meta.app_label,
                app_label = Image._meta.app_label,
                name='Image'
            )
            add_image_permission = Permission.objects.get(codename='add_image', content_type=image_type)
            add_album_permission = Permission.objects.get(codename='add_album', content_type=album_type)
            change_image_permission = Permission.objects.get(codename='change_image', content_type=image_type)
            change_album_permission = Permission.objects.get(codename='change_album', content_type=album_type)
            delete_image_permission = Permission.objects.get(codename='delete_image', content_type=image_type)
            delete_album_permission = Permission.objects.get(codename='delete_album', content_type=album_type)
            instance.user_permissions.add(add_image_permission, add_album_permission,)
            instance.user_permissions.add(change_image_permission, change_album_permission,)
            instance.user_permissions.add(delete_image_permission, delete_album_permission,)
        except ObjectDoesNotExist:
            # Permissions are not yet installed or conten does not created yet
            # probaly this is first
            pass


if SELF_MANAGE:
    post_save.connect(setup_imagestore_permissions, User)
