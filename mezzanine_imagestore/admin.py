from django.conf import settings
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from sorl.thumbnail.admin import AdminInlineImageMixin

from imagestore.models import Image, Album, AlbumUpload, AlbumImage
from forms import AlbumAdminForm, ImageAdminForm, ZipImageAdminForm, InlineImageForm
from helpers.string import reverse_slug


class FilterUserAdmin(admin.ModelAdmin): 
    def queryset(self, request): 
        qs = super(FilterUserAdmin, self).queryset(request) 
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            # the changelist itself
            return True

        if request.user.is_superuser:
            return True
        else:
            return obj.user == request.user

    has_delete_permission = has_change_permission


class InlineImageAdmin(AdminInlineImageMixin, admin.TabularInline):
    form = InlineImageForm
    model = AlbumImage
    fields = ('mediafile', 'image', 'order')
    extra = 0


class AlbumAdmin(FilterUserAdmin):
    form = AlbumAdminForm
    fields = ('name', 'user', 'is_public')
    list_display = ('name', 'owner', 'admin_thumbnail', 'image_count', 'is_public', 'order')
    list_editable = ('order', 'is_public')
    list_filter = ('user', 'is_public')
    inlines = [InlineImageAdmin]

    class Media:
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        js = [static_url + 'imagestore/admin/js/change-album.js',]

    def owner(self, obj):
        return obj.user.get_full_name()

    def queryset(self, request):
        qs = super(AlbumAdmin, self).queryset(request) 
        return qs.annotate(image_count=Count('images'))

    def image_count(self, inst):
        return inst.image_count
    image_count.admin_order_field = 'image_count'

admin.site.register(Album, AlbumAdmin)


class ImageAdmin(FilterUserAdmin):
    form = ImageAdminForm
    fieldsets = ((None, {'fields': ['mediafile', 'image', 'title', 'description', 'user', 'tags']}),)
    list_display = ('admin_thumbnail', 'title', 'user')
    list_filter = ('user', 'albums', )
    list_editable = ('title', )

    class Media:
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        js = [static_url + 'imagestore/admin/js/add-image.js',]

    def save_model(self, request, obj, form, change):
        """
        Assign filename as title if not supplied
        """
        if not obj.title:
            obj.title = reverse_slug(request.FILES['image'].name, remove_extension=True, title=True)

        if not obj.user:
            obj.user = request.user
        obj.save()


class AlbumUploadAdmin(admin.ModelAdmin):
    form = ZipImageAdminForm
    fields = ('zip_file', ('new_album_name', 'user'), 'album', 'tags')

    class Media:
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        js = [static_url + 'imagestore/admin/js/add-albumupload.js',]

    def has_change_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user

        """
        Assign filename as title if not supplied
        """
        if not obj.new_album_name:
            obj.new_album_name = obj.user.get_full_name() \
                + ' ' + reverse_slug(request.FILES['zip_file'].name, remove_extension=True, title=True) 
        obj.save()

    def response_add(self, request, obj, post_url_continue=None):
        post_url_continue = reverse("admin:imagestore_album_change", args=(obj.album.pk,))
        obj.delete()
        return HttpResponseRedirect(post_url_continue)


IMAGE_MODEL = getattr(settings, 'IMAGESTORE_IMAGE_MODEL', None)
if not IMAGE_MODEL:
    admin.site.register(Image, ImageAdmin)

ALBUM_MODEL = getattr(settings, 'IMAGESTORE_ALBUM_MODEL', None)
if not ALBUM_MODEL:
    admin.site.register(AlbumUpload, AlbumUploadAdmin)
