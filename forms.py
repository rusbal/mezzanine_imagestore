#!/usr/bin/env python
# vim:fileencoding=utf-8
try:
    import autocomplete_light
    AUTOCOMPLETE_LIGHT_INSTALLED = True
except ImportError:
    AUTOCOMPLETE_LIGHT_INSTALLED = False

from imagestore.middleware.request import get_request

__author__ = 'zeus'

import zipfile

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from sorl.thumbnail.admin.current import AdminImageWidget

from models import Image, Album


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class AlbumOwnerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name_with_owner()


class AlbumOwnerMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name_with_owner()


class ReadOnlyValueWidget(forms.TextInput):
    def render(self, name, value, attrs=None): 
        inputfield = super(ReadOnlyValueWidget, self).render(name, value, attrs)
        if value:
            try:
                user = User.objects.get(pk=value)
            except User.DoesNotExist:
                return inputfield 
            return mark_safe(user.get_full_name() + "<input type='hidden' id='id_user' name='user' value='{0}'>".format(value)) 
        return inputfield


class MediaFileWidget(forms.TextInput):
    """
    COPIED FROM FeinCMS code
    TextInput widget, shows a link to the current value if there is one.
    """ 
    def render(self, name, value, attrs=None): 
        inputfield = super(MediaFileWidget, self).render(name, value, attrs)
        if value:
            try:
                mf = Image.objects.get(pk=value)
            except Image.DoesNotExist:
                return inputfield 
            return mark_safe(mf.admin_thumbnail()) 
        return inputfield


class InlineImageForm(forms.ModelForm):
    mediafile = forms.ModelChoiceField(queryset=Image.objects.all(),
                                       widget=MediaFileWidget(attrs={'class': 'image-fk'}),
                                       label=_('image file'),
                                       required=False)
    order = forms.IntegerField(label=_('order'),
                               required=False)

    class Meta:
        model = Image

    def __init__(self, *args, **kwargs):
        super(InlineImageForm, self).__init__(*args, **kwargs)
        try:
            image = Image.objects.get(pk=self.instance.image_id)
            self.fields["mediafile"].initial = image.pk
        except:
            pass

        """
        Build selection according to Album owner
        """
        qi = Image.objects.all()
        owner = get_request().user
        if not owner.is_superuser:
            qi = qi.filter(user=owner) 
        self.fields['image'].choices = [(u'',u'----------')] + [(img.pk, img.__unicode__()) for img in qi]

    def clean_image(self):
        data = self.cleaned_data
        post = get_request().POST 
        if int(post['user']) != data['image'].user.pk: 
            raise forms.ValidationError(_("Please select an image that belongs to Album Owner.")) 
        return data['image']


class AlbumAdminForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True).all(),
                                  widget=ReadOnlyValueWidget(),
                                  label=_('Owner')) 
    name = forms.CharField()
    is_public = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(AlbumAdminForm, self).__init__(*args, **kwargs)

        if not 'instance' in  kwargs:
            """
            Adding a new Album
            """
            qu = User.objects.filter(is_active=True)
            owner = get_request().user
            if not owner.is_superuser:
                qu = qu.filter(pk=owner.pk)
            self.fields['user'] = UserChoiceField(queryset=qu) 
            self.fields['user'].label = _('Owner')


"""
Used in views.py
""" 
class AlbumForm(forms.ModelForm):
    class Meta(object):
        model = Album
        exclude = ('user', 'created', 'updated')

    def __init__(self, *args, **kwargs):
        super(AlbumForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs and kwargs['instance']:
            self.fields['head'].queryset = Image.objects.filter(album=kwargs['instance'])
        else:
            self.fields['head'].widget = forms.HiddenInput() 


class ImageAdminForm(forms.ModelForm):
    mediafile = forms.ModelChoiceField(queryset=Image.objects.all(),
                                       widget=MediaFileWidget(attrs={'class': 'image-fk'}),
                                       label=_('image file'),
                                       required=False)

    class Meta:
        model = Image

    def __init__(self, *args, **kwargs):
        super(ImageAdminForm, self).__init__(*args, **kwargs)

        self.fields['title'].required = False

        qu = User.objects.filter(is_active=True)
        owner = get_request().user
        if not owner.is_superuser:
            qu = qu.filter(pk=owner.pk)
        self.fields['user'] = UserChoiceField(queryset=qu)
        self.fields['user'].required = False

        self.fields['mediafile'].initial = self.instance.pk


"""
Used in views.py
""" 
class ImageForm(forms.ModelForm):
    class Meta(object):
        model = Image
        exclude = ('user', 'order')

    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'cols': 19}), required=False,
                                  label=_('Description'))

    def __init__(self, user, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        self.fields['album'].queryset = Album.objects.filter(user=user)
        self.fields['album'].required = True
        if AUTOCOMPLETE_LIGHT_INSTALLED:
            self.fields['tags'].widget = autocomplete_light.TextWidget('TagAutocomplete')


class ZipImageAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ZipImageAdminForm, self).__init__(*args, **kwargs)

        owner = get_request().user

        qa = Album.objects.all().order_by('user__first_name', 'name')
        qu = User.objects.filter(is_active=True)

        if not owner.is_superuser:
            qa = qa.filter(user=owner)
            qu = qu.filter(pk=owner.pk)

        self.fields['album'] = AlbumOwnerChoiceField(queryset=qa) 
        self.fields['album'].required = False

        self.fields['user'] = UserChoiceField(queryset=qu)
        self.fields['user'].required = False
        self.fields['user'].label = _('Owner')

    def clean_zip_file(self):
        data = self.cleaned_data

        """
        Python 2.7
        """
        # if not zipfile.is_zipfile(data['zip_file'].file):
        #     raise forms.ValidationError("Please select a zip file.")

        """
        Python 2.6
        """
        try:
            zip = zipfile.ZipFile(data['zip_file'].file)
        except zipfile.BadZipfile:
            raise forms.ValidationError("Please select a zip file.")

        return data['zip_file']

    def clean(self):
        data = self.cleaned_data

        if data['album']: 
            if data['new_album_name'] or data['user']:
                raise forms.ValidationError("Please either enter a new album name/owner or select an existing album but not both.")
        else:
            if not data['user']:
                if data['new_album_name']:
                    raise forms.ValidationError("Please select owner of %s." % data['new_album_name']) 
                else:
                    raise forms.ValidationError("Please select owner.") 
        
        return data
