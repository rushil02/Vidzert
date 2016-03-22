from django.shortcuts import render
from .models import *
from ipware.ip import get_real_ip
from django.http import HttpResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
from video.models import Video
from promoter.models import PromoterProfile, PromoterAccount
from promoter_transaction.models import PromoterTransactionLog
from client_transaction.models import ClientTransactionLog
from logs.models import VideoUnsubscribedLog
from client.models import ClientProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
import datetime
from django.db.models import Sum, Count, Q
from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseNotFound
from user_login.forms import UserCreationForm
from views_2 import log_error, log_activity
from django.contrib.auth import authenticate, login
from .tasks import send_mail_async, send_sms_async
from client.views import profile_insights


@user_passes_test(lambda u: u.is_superuser)
def home(request):
    promoter_count = PromoterProfile.objects.filter(promoter_id__is_active=True).count()
    active_video_count = Video.objects.get_active()
    inactive_video_count = Video.objects.filter(active=False).count()
    featured_video_count = Video.objects.get_featured().count()
    non_featured_video_count = Video.objects.get_active().exclude(featured=True).count()

    # New Promoters this week
    week = datetime.datetime.now().date() - datetime.timedelta(days=7)
    new_promoters_week = PromoterProfile.objects.filter(create_time__gte=week).count()

    total_expense = PromoterTransactionLog.objects.all().annotate(expense=Sum('amount'))

    total_sales = ClientTransactionLog.objects.all().annotate(sales=Sum('amount'))

    backlinks_week = VideoUnsubscribedLog.objects.filter(promoter_id__isnull=True, create_time__gte=week)

    anonymous_week = VideoUnsubscribedLog.objects.filter(promoter_id__isnull=False, create_time__gte=week)

    latest_videos = Video.objects.order_by('-create_time').select_related('videoinsights', 'videoaccount')

    latest_clients = ClientProfile.objects.order_by('-create_time')[:5]

    truncate_date = connection.ops.date_trunc_sql('month', 'create_time')
    qs = Video.objects.extra({'month': truncate_date})
    # Sales per Month
    report = qs.values('month').annotate(Sum('videoaccount__video_cost'), Count('pk')).order_by('month')

    return HttpResponse("Admin Panel")


def send_notifications():  # TODO
    recipient_list = PromoterProfile.objects.get_all_mail_recipients()
    send_mail_async.delay(subject='Video release notification', message='video will be released on',
                          recipients=recipient_list)
    send_sms_async.delay(message='Video will be released on', mobile_num=9811)


# def set_authorise_video(video):
#     video.authorised = True
#     video.save()
#
#
# def set_video_paid(video):
#     video.paid = True
#     video.save()


# def send_registration_email(my_user):
#     subject, from_email, recipient = 'Vidzert Account Verification', 'from@example.com', my_user.email
#     text_content = 'This is an important message.'
#     html_content = '<a href="enter link here">Click here for verification</a>'
#     send_mail(subject, text_content, 'from@example.com', [recipient], fail_silently=False, html_message=html_content)


# TODO: perk- Advanced Notification mail
def send_advanced_notification_mail(video, time):
    recipients = PromoterProfile.objects.get_all_mail_recipients()
    if recipients:
        subject = 'New Video Going To Be Uploaded'
        message = 'Video Name - ' + video.name + '\n' + \
                  'Upload time - ' + time + '\n' + \
                  'Maximum Coins - ' + video.max_coins
        send_mail_async.delay(subject, message, recipients)
        send_sms_async.delay(message='Video will be released on', mobile_num=9811)
        PromoterAccount.objects.set_mail_notification_flag()


@user_passes_test(lambda u: u.is_superuser)
def video_insights(request, video_uuid):
    try:
        video = Video.objects.get_video(video_uuid)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('<h1>Page not found</h1>')
    video_list = []

    (gender_insight, state_insight, gender_engagement_insight, state_engagement_insight,
     age_insights) = profile_insights(video)
    video_insight = video.videoinsights
    video_list.append({
        "video": video,
        "video_insights": video_insight,
        "gender_insight": gender_insight,
        "state_insight": state_insight,
        "gender_engagement_insight": gender_engagement_insight,
        "state_engagement_insight": state_engagement_insight,
        "age_insights": age_insights
    })

    child_videos = video.get_child_videos()
    for child_video in child_videos:
        (child_gender_insight, child_state_insight, child_gender_engagement_insight, child_state_engagement_insight,
         child_age_insights) = profile_insights(child_video)
        child_video_insights = child_video.videoinsights
        video_list.append({
            "video": child_video,
            "video_insights": child_video_insights,
            "gender_insight": child_gender_insight,
            "state_insight": child_state_insight,
            "gender_engagement_insight": child_gender_engagement_insight,
            "state_engagement_insight": child_state_engagement_insight,
            "age_insights": child_age_insights
        })
    context = {
        "video": video,
        "video_list": video_list
    }
    return render(request, 'client/video_insight.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_registration(request):
    sign_up_form = UserCreationForm(request.POST or None)
    if sign_up_form.is_valid() and request.POST:
        user = sign_up_form.save(commit=False)
        user.user_type = 'S'
        user.is_staff = True
        user.save()
        return HttpResponse("Staff user created")
    else:
        context = {
            "form": sign_up_form
        }
        return render(request, 'client_registration.html', context)


# @user_passes_test(lambda u: u.is_superuser)
# def force_terminate(request):
