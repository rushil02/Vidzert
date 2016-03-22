from django.forms import ModelForm
from django import forms
from .models import Video, VideoCategory, VideoInfo, VideoProfile, VideoAccount, VideoFile
from django.utils.translation import ugettext_lazy as _
from cities_light.models import Region
from django.contrib.postgres.forms import IntegerRangeField
from video.upload_video_check import check_video_inst


class VideoUploadForm(ModelForm):
    category = forms.ModelMultipleChoiceField(queryset=VideoCategory.objects.all())

    class Meta:
        model = Video
        fields = ['name', 'featured', 'publisher', 'category', ]


class VideoInfoForm(ModelForm):
    class Meta:
        model = VideoInfo
        fields = ['desc', 'banner_landing_page', 'banner_landing_page_image', 'product_desc',
                  'buy_product', ]
        labels = {
            'desc': _('Description'),
            'banner_landing_page': _('Banner Landing Page URL'),
            'banner_landing_page_image': _('Banner Landing Page Image'),
            'product_desc': _('Product Description URL'),
            'buy_product': _('Buy Product URL'),
        }


class VideoProfileForm(ModelForm):
    age = IntegerRangeField()
    state = forms.ModelMultipleChoiceField(queryset=Region.objects.all(), required=False)

    class Meta:
        model = VideoProfile
        fields = ['age', 'gender', 'city', 'state', ]


class VideoAccountForm(ModelForm):
    class Meta:
        model = VideoAccount
        fields = ['video_cost']
        labels = {
            'video_cost': _('Video Cost'),
        }

    # TODO: Set minimum applicable video cost
    def clean_video_cost(self):
        cost = self.cleaned_data['video_cost']
        if int(cost) <= 1000:
            raise forms.ValidationError(_("Minimum amount is Rs.1000/-"), code="Invalid Cost")
        else:
            return cost


class VideoFileForm(ModelForm):
    class Meta:
        model = VideoFile
        fields = ['video_file_orig', 'thumbnail_image']
        labels = {
            'video_file_orig': _('Video File'),
        }

    def clean_video_file_orig(self):
        min_size = 2.5 * 1024 * 1024
        max_size = 400 * 1024 * 1024
        video_file_orig = self.cleaned_data['video_file_orig']
        if video_file_orig.size < min_size:
            raise forms.ValidationError(_("Video should be at least 2.5 MB."))
        elif video_file_orig.size > max_size:
            raise forms.ValidationError(_("Video should be less than 400 MB. "))
        else:
            temp_path = video_file_orig.temporary_file_path()
            error, error_list = check_video_inst(temp_path)

            if error == "File corrupt":
                raise forms.ValidationError(_("Initial checks failed, Unrecognized file format/codec"),
                                            code="Invalid Video")

            elif error == "Validation errors":
                print "validation error found"
                raise forms.ValidationError([forms.ValidationError(_(error)) for error in error_list])

            else:
                return self.cleaned_data['video_file_orig']


class VideoReviseForm(ModelForm):
    class Meta:
        model = Video
        fields = ['featured']
