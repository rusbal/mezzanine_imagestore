#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'


from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from sorl.thumbnail import get_thumbnail
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

from imagestore.utils import get_model_string


SELF_MANAGE = getattr(settings, 'IMAGESTORE_SELF_MANAGE', True)


class BaseAlbum(models.Model):
    class Meta(object):
        abstract = True
        ordering = ('order', 'created', 'name')
        permissions = (
            ('moderate_albums', 'View, update and delete any album'),
        )
        unique_together = ('user', 'name')

    user = models.ForeignKey(User, verbose_name=_('Owner'), related_name='albums')
    name = models.CharField(_('Name'), max_length=100, blank=False, null=False)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)
    is_public = models.BooleanField(_('Is public'), default=True)
    head = models.ForeignKey(get_model_string('Image'), related_name='head_of', null=True, blank=True, on_delete=models.SET_NULL)

    order = models.IntegerField(_('Order'), default=0)

    def get_head(self):
        if self.head:
            return self.head
        else:
            if self.images.all().count()>0:
                self.head = self.images.all()[0]
                self.save()
                return self.head
            else:
                return None

    def set_head(self, id, head):
        self.head = head
        self.save()

    @permalink
    def get_absolute_url(self):
        return 'imagestore:album', (), {'album_id': self.id}

    def __unicode__(self):
        return self.name

    def admin_thumbnail(self):
        img = self.get_head()
        if img:
            try:
                return '<img src="%s">' % get_thumbnail(img.image, '100x100', crop='center').url
            except IOError:
                logger.exception('IOError for album %s', img.image)
                return 'IOError'
        return _('Empty album')

    admin_thumbnail.short_description = _('Head')
    admin_thumbnail.allow_tags = True

    def name_with_owner(self):
        full_name = self.user.get_full_name() or self.user.username
        return self.name + ' (' + full_name + ')'
