from django.test import TestCase
from video.models import *
from video.forms import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


# Create your tests here.


class ProfilingTestCase(TestCase):
    user_email = 'client@client.com'
    user_password = 'root'
    name = 'ABC'
    user_type = 'C'

    video_upload_to_path = '2015/10/10/48027df8-eed4-4689-8c67-50fc8d161d0d.MP4'

    def setUp(self):
        self.define_groups_and_perms()
        self.define_video_categories()

    def define_groups_and_perms(self):
        # Create groups
        promoter, promoter_create_time = Group.objects.get_or_create(name='Promoter')
        client, client_create_time = Group.objects.get_or_create(name='Client')
        staff, staff_create_time = Group.objects.get_or_create(name='Staff')

        # Get permissions
        permissions = Permission.objects.filter(codename__startswith="change")

        # Create permissions if any extra than add, change, delete

        # Can access promoter
        promoter_content_type = ContentType.objects.get(app_label='promoter', model='promoterprofile')
        can_access_promoter, pr_create_time = Permission.objects.get_or_create(name='Can access promoter',
                                                                               codename='access_promoter',
                                                                               content_type=promoter_content_type)

        # Can access Client
        client_content_type = ContentType.objects.get(app_label='client', model='clientprofile')
        can_access_client, cl_create_time = Permission.objects.get_or_create(name='Can access client',
                                                                             codename='access_client',
                                                                             content_type=client_content_type)

        # Can access Staff
        staff_content_type = ContentType.objects.get(app_label='staff_custom', model='staffprofile')
        can_access_staff, st_create_time = Permission.objects.get_or_create(name='Can access staff',
                                                                            codename='access_staff',
                                                                            content_type=staff_content_type)

        # Set permissions to groups
        staff.permissions = permissions
        staff.permissions.add(can_access_staff)
        promoter.permissions = [can_access_promoter]
        client.permissions = [can_access_client]

    def define_video_categories(self):
        # Define all categories here
        VideoCategory.objects.get_or_create(category_name='BC BC')
        VideoCategory.objects.get_or_create(category_name='Technology')
        VideoCategory.objects.get_or_create(category_name='Music')

    def create_client(self):
        return get_user_model().objects.create_user(self.user_email, self.name, self.user_type, self.user_password)

    def test_user_creation(self):
        # Create a new user saving the time frame
        before_creation = timezone.now()
        self.client = self.create_client()
        after_creation = timezone.now()

        # Check user exists and email is correct
        self.assertEqual(get_user_model().objects.all().count(), 1)
        self.assertEqual(get_user_model().objects.all()[0].email, self.user_email)

        # Check date_joined, date_modified and last_login dates
        # self.assertLess(before_creation, get_user_model().objects.all()[0].date_joined)
        # self.assertLess(get_user_model().objects.all()[0].date_joined, after_creation)

        # self.assertLess(before_creation, get_user_model().objects.all()[0].last_login)
        # self.assertLess(get_user_model().objects.all()[0].last_login, after_creation)

        # Check flags
        self.assertTrue(get_user_model().objects.all()[0].is_active)
        self.assertFalse(get_user_model().objects.all()[0].is_staff)
        self.assertFalse(get_user_model().objects.all()[0].is_superuser)

    def test_upload(self):
        all_categories = VideoCategory.objects.all()
        data = {
            'name': 'Sappy',
            'video_file': self.video_upload_to_path,
            'publisher': 'Nirvana',
            'category': all_categories
        }
        form = VideoUploadForm(data)
        self.assertTrue(form.is_valid())
        video = form.save(commit=False)
        video.client_id = self.client
        video.save()
        form.save_m2m()

        data = {}
        video_info_form = VideoInfoForm(data)
        self.assertTrue(video_info_form.is_valid())
        video_info = video_info_form.save(commit=False)
        video_info.video_id = video
        video_info.save()

        video_profile_form = VideoProfileForm(data)
        self.assertTrue(video_profile_form.is_valid())
        video_profile = video_profile_form.save(commit=False)
        video_profile.video_id = video
        video_profile.save()
        video_profile_form.save_m2m()

        data = {
            'video_cost': 10000
        }
        video_account_form = VideoAccountForm(data)
        self.assertTrue(video_account_form.is_valid())
        video_account = video_account_form.save(commit=False)
        video_account.video_id = video
        video_account.save()