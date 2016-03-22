from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from graph.models import GraphCreationMeta
from perks.models import Perks
from video.models import VideoCategory


def define_groups_and_perms():
    # Create groups
    promoter, promoter_created = Group.objects.get_or_create(name='Promoter')
    client, client_created = Group.objects.get_or_create(name='Client')
    staff, staff_created = Group.objects.get_or_create(name='Staff')

    # Get permissions
    permissions = Permission.objects.filter(codename__startswith="change")

    # Create permissions if any extra than add, change, delete

    # Can access promoter
    promoter_content_type = ContentType.objects.get(app_label='promoter', model='promoterprofile')
    can_access_promoter, pr_created = Permission.objects.get_or_create(name='Can access promoter',
                                                                       codename='access_promoter',
                                                                       content_type=promoter_content_type)

    # Can access Client
    client_content_type = ContentType.objects.get(app_label='client', model='clientprofile')
    can_access_client, cl_created = Permission.objects.get_or_create(name='Can access client',
                                                                     codename='access_client',
                                                                     content_type=client_content_type)

    # Can access Staff
    staff_content_type = ContentType.objects.get(app_label='staff_custom', model='staffprofile')
    can_access_staff, st_created = Permission.objects.get_or_create(name='Can access staff',
                                                                    codename='access_staff',
                                                                    content_type=staff_content_type)

    # Set permissions to groups
    staff.permissions = permissions
    staff.permissions.add(can_access_staff)
    promoter.permissions = [can_access_promoter]
    client.permissions = [can_access_client]


# Create all type of Perks here
def create_perks():
    # Add and define all perks here
    Perks.objects.get_or_create(perk_id=1, name='Double up', cost=30, block='L')
    Perks.objects.get_or_create(perk_id=2, name='Coin Magnet', cost=50, block='L')
    Perks.objects.get_or_create(perk_id=3, name='Position Wildcard', cost=100, block='F')
    Perks.objects.get_or_create(perk_id=4, name='Time Wildcard', cost=75, block='F')
    Perks.objects.get_or_create(perk_id=5, name='Advanced Notification', cost=15, block='M')
    Perks.objects.get_or_create(perk_id=6, name='Highest Peak Notification', cost=30, block='M')


# Define all Video Categories here
def define_video_categories():  # TODO: define all categories
    # Define all categories here
    VideoCategory.objects.get_or_create(category_name='BC BC')


# Define the settings for first Video Graph and Survey Graph
def define_first_graph_meta():
    # win_models -> dictionary {win_model_percentage: probability} ===>> check for summation(probability) = 1
    video_graph_meta = {"init_peak": "0.01", "load_balancer_value": "100", "base_limit": "0.50",
                        "per_person_cost": "1.0", "expense_percentage": "0.70", "featured_cost_percentage": "0.10"}
    video_graph_win_model = {"0.005": "0.2", "0.0075": "0.1", "0.0025": "0.3", "0.001": "0.4"}
    #  FIXME
    survey_graph_meta = {"init_peak": "0.01", "load_balancer_value": "1000", "base_limit": "20.00",
                         "per_person_cost": "50.0", "expense_percentage": "0.70", "featured_cost_percentage": "0.10"}
    survey_graph_win_model = {"0.005": "0.2", "0.0075": "0.1", "0.0025": "0.3", "0.001": "0.4"}

    flag1, error_meta = GraphCreationMeta.objects.create_graph_meta(graph_type='V', graph_meta=video_graph_meta,
                                                                    graph_win_model=video_graph_win_model)

    flag2, error_meta = GraphCreationMeta.objects.create_graph_meta(graph_type='S', graph_meta=survey_graph_meta,
                                                                    graph_win_model=survey_graph_win_model)
    if (flag1 is False) or (flag2 is False):
        raise AssertionError


class Command(BaseCommand):
    help = 'Initialize website with user settings and details'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                define_groups_and_perms()
                create_perks()
                define_video_categories()
                define_first_graph_meta()
                self.stdout.write("Website initialized with data")
        except:
            raise CommandError("Some problem occurred. Rolling back changes, please initialize again.")
