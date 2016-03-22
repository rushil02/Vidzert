from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect
from ipware.ip import get_real_ip
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from models import PromoterProfile, PromoterPerks
from video.views import watch
from forms import ProfileForm
from django.db import transaction
from perks.views import double_up, magnet, position_wildcard
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_POST, require_GET
import time
from video.models import Video
from survey.models import Survey, Answer
from survey.forms import QuestionSetAnswerForm
from logs.models import VideoPromoterLog, VideoPromoterReplayLog, VideoPromoterPerkLog, PerkTransactionLog, \
    DurationWatchedLog, SurveyPromoterLog
from perks.models import Perks
from admin_custom.models import ErrorLog, ActivityLog


# Create your views here.


@permission_required('promoter.access_promoter')
def home(request):
    try:
        user = request.user
        promoter = PromoterProfile.objects.select_related('promoteraccount').get(promoter_id=user)
        promoter_account = promoter.promoteraccount
    except ObjectDoesNotExist:
        error_meta = {
            "method": "promoter.views.home",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')

    video_list = promoter.profile_v2()

    (pre_perks, post_perks) = promoter_account.get_graph_perks()

    # Paginator
    paginator = Paginator(video_list, 12)  # Show 12 contacts per page

    page = request.GET.get('page')
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        videos = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        videos = paginator.page(paginator.num_pages)

    context = {
        "user": request.user.name,
        "queryset": videos,
        "pre_perk": pre_perks,
        "post_perk": post_perks,
    }

    activity_meta = {
        "method": "promoter.views.home",
        "page_number": request.GET.get('page')
    }
    ActivityLog.objects.create_log(request, "Promoter Homepage", activity_meta)
    return render(request, 'promoter/main.html', context)


@permission_required('promoter.access_promoter')
def watched(request):
    try:
        promoter = request.user.promoterprofile
    except PromoterProfile.DoesNotExist:
        error_meta = {
            "method": "promoter.views.watched",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')

    logs = promoter.videopromoterlog_set \
        .order_by('create_time') \
        .select_related('video_id', 'video_id__videofile__thumbnail_image') \
        .filter(video_id__parent_video__isnull=True) \
        .values('video_id__videofile__thumbnail_image', 'video_id__uuid',
                'video_id__name', 'video_id__max_coins',
                'video_id__publisher', 'coins')
    context = {
        "logs": logs
    }
    activity_meta = {
        "method": "promoter.views.watched",
    }
    ActivityLog.objects.create_log(request, "Promoter Watched Videos", activity_meta)
    return render(request, 'promoter/watched.html', context)


@permission_required('promoter.access_promoter')
@require_GET
def redirection(request):
    if not request.GET.get('link') or not request.GET.get('video_uuid'):
        error_meta = {
            "method": "promoter.views.redirection",
        }
        ErrorLog.objects.create_log(request=request, error_code=1, error_type="NoGet", error_meta=error_meta)
        raise SuspiciousOperation('Error Code: 1')
    else:
        link = request.GET.get('link')
        video_uuid = request.GET.get('video_uuid')
        try:
            video = Video.objects.get_video(video_uuid)
        except (Video.DoesNotExist, ValueError):
            error_meta = {
                "method": "promoter.views.redirection",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=3, error_type="Video Object Error",
                                        error_meta=error_meta)
            raise SuspiciousOperation('Error Code: 3')
        try:
            promoter = request.user.promoterprofile
        except PromoterProfile.DoesNotExist:
            error_meta = {
                "method": "promoter.views.redirection",
            }
            ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
            raise SuspiciousOperation('Error Code: 4')

        # Increment of engagement column for profiling in different categories - In Promoter.views
        promoter.promoter_profiling(video, 1)
        # Increment Video Insights
        video.increment_insights_redirection_click()
        activity_meta = {
            "method": "promoter.views.redirection",
            "link": request.GET.get('link'),
            "video_uuid": request.GET.get('video_uuid')
        }
        ActivityLog.objects.create_log(request, "Promoter Engagement", activity_meta)
        return redirect(link)


@permission_required('promoter.access_promoter')
def promoter_account_view(request):
    try:
        user = request.user
        promoter = PromoterProfile.objects.select_related('promoteraccount').get(promoter_id=user)
        promoter_account = promoter.promoteraccount
    except ObjectDoesNotExist:
        error_meta = {
            "method": "promoter.views.promoter_account_view",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')
    perks = promoter_account.get_perks()
    context = {
        "profile": promoter,
        "perks": perks
    }
    activity_meta = {
        "method": "promoter.views.promoter_account_view",
    }
    ActivityLog.objects.create_log(request, "Promoter View Account", activity_meta)
    return render(request, "promoter/promoter_profile.html", context)


@permission_required('promoter.access_promoter')
def update_profile(request):
    try:
        promoter = request.user.promoterprofile
    except PromoterProfile.DoesNotExist:
        error_meta = {
            "method": "promoter.views.update_profile",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')
    form = ProfileForm(request.POST or None, instance=promoter)
    context = {
        "form": form
    }
    if request.POST:
        if form.is_valid():
            form.save()
            activity_meta = {
                "method": "promoter.views.update_profile",
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, "Update Promoter Account", activity_meta)
            return redirect('/pr/account/')
        else:
            return render(request, "promoter/edit_profile.html", context)
    else:
        activity_meta = {
            "method": "promoter.views.update_profile",
        }
        ActivityLog.objects.create_log(request, "Update Promoter Account", activity_meta)
        return render(request, "promoter/edit_profile.html", context)


@require_POST
@permission_required('promoter.access_promoter')
@ensure_csrf_cookie
@transaction.atomic
def video_viewed(request):
    if request.POST.get('video_uuid') and request.session.get('video_id'):
        video_uuid = request.POST.get('video_uuid')
        pre_perk = None
        post_perk = None
        promoter_pre_perk_obj = None
        promoter_post_perk_obj = None
        position = None
        x_data = []
        y_data = []
        coins = 0
        fake_coins = 0
        quantity = 1
        # check if not a bot

        try:
            user = request.user
            promoter = PromoterProfile.objects.select_related('promoteraccount').get(promoter_id=user)
            promoter_account = promoter.promoteraccount
        except ObjectDoesNotExist:
            error_meta = {
                "method": "promoter.views.video_viewed",
            }
            ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
            return JsonResponse({"status_code": 4})

        try:
            video = Video.objects.select_related('videoaccount', 'videoinsights').get_from_uuid(video_uuid)
            video_account = video.videoaccount
            video_insights = video.videoinsights
        except (ObjectDoesNotExist, ValueError):
            error_meta = {
                "method": "promoter.views.video_viewed",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=3, error_type="Video Object Error",
                                        error_meta=error_meta)
            return JsonResponse({"status_code": 3})

        video_id = request.session.pop('video_id')
        video_duration = float(request.session.pop('video_duration'))
        start_time = request.session.pop('start_time')
        current_time = time.time()

        watched_time = current_time - start_time

        if (video.id != video_id) or (watched_time < video_duration):
            error_meta = {
                "method": "promoter.views.video_viewed",
                "video_id": str(video.id),
                "session_video_id": str(video_id),
                "watched_time": str(watched_time),
                "video_duration": str(video_duration)
            }
            ErrorLog.objects.create_log(request=request, error_code=31, error_type="Promoter Watch session error",
                                        error_meta=error_meta)
            return JsonResponse({"status_code": 31})
        else:

            ip = get_real_ip(request)
            device_type = "C"

            # share link generation
            share_link = '/watch/{0}/{1}'.format(video.slug, promoter.uuid)

            total_views = video_insights.total_views()

            if promoter.check_video_watched(video):

                # increment in profiling of promoter
                promoter.promoter_profiling(video, 2)

                VideoPromoterReplayLog.objects.replay_video_log_entry(video, promoter, ip, device_type)

                activity_meta = {
                    "method": "promoter.views.video_viewed",
                    "video_id": str(video.id),
                    "start_time": str(start_time),
                    "end_time": str(current_time),
                    "watched_time": str(watched_time),
                    "video_duration": str(video_duration)
                }
                ActivityLog.objects.create_log(request, "Promoter Video Replay", activity_meta)

                response = JsonResponse({"share_link": share_link, "status_code": 69})

            else:
                # Check if video inactive while promoter watches a video
                if video_account.max_viewership <= total_views or video.active is False:
                    # increment of views
                    video.increment_views_promoter()
                    # local variable
                    total_views += 1
                    # increment in profiling of promoter
                    promoter.promoter_profiling(video, 2)
                    # log entry
                    VideoPromoterLog.objects.promoter_log_entry(video, promoter, ip, share_link, coins, total_views,
                                                                device_type)

                    response = JsonResponse({"share_link": share_link,
                                             "status_code": 32})

                else:
                    # Retrieve graph
                    graph = video_account.graph_id

                    if request.session.get('post_perk_id'):
                        post_perk_id = request.session.pop('post_perk_id')
                        try:
                            post_perk = Perks.objects.get_perk_object(post_perk_id)
                        except (Perks.DoesNotExist, ValueError):
                            error_meta = {
                                "method": "promoter.views.video_viewed",
                                "post_perk_id": str(post_perk_id)
                            }
                            ErrorLog.objects.create_log(request=request, error_code=33,
                                                        error_type="Post Perk Not exist", error_meta=error_meta)
                            return JsonResponse({"status_code": 33})

                        try:
                            promoter_post_perk_obj = PromoterPerks.objects.get(perk_id=post_perk, quantity__gt=0)
                        except PromoterPerks.DoesNotExist:
                            error_meta = {
                                "method": "promoter.views.video_viewed",
                                "post_perk_id": str(post_perk_id)
                            }
                            ErrorLog.objects.create_log(error_code=37, error_type="Promoter Perk Application Error",
                                                        error_meta=error_meta, request=request)
                            return JsonResponse({"status_code": 37})

                    if request.session.get('pre_perk_id'):
                        pre_perk_id = request.session.pop('pre_perk_id')
                        try:
                            pre_perk = Perks.objects.get_perk_object(pre_perk_id)
                        except Perks.DoesNotExist:
                            error_meta = {
                                "method": "promoter.views.video_viewed",
                                "pre_perk_id": str(pre_perk_id)
                            }
                            ErrorLog.objects.create_log(request=request, error_code=34, error_type="Pre Perk Not exist",
                                                        error_meta=error_meta)
                            return JsonResponse({"status_code": 34})

                        if request.session.get('position') and request.session.get('quantity'):
                            position = request.session.pop('position')
                            quantity = request.session.pop('quantity')

                        try:
                            promoter_pre_perk_obj = PromoterPerks.objects.get(perk_id=pre_perk, quantity__gte=quantity)
                        except PromoterPerks.DoesNotExist:
                            error_meta = {
                                "method": "promoter.views.video_viewed",
                                "pre_perk_id": str(pre_perk_id)
                            }
                            ErrorLog.objects.create_log(error_code=37, error_type="Promoter Perk Application Error",
                                                        error_meta=error_meta, request=request)
                            return JsonResponse({"status_code": 37})

                    # Apply pre perks
                    if pre_perk:
                        if pre_perk.perk_id == 3:
                            (fake_x_data, fake_y_data, coins) = position_wildcard(pre_perk, graph, position, quantity)
                            (x_data, y_data, fake_coins) = graph.get_pos(total_views + 1)
                            if coins > (quantity * 5000):
                                coins = (quantity * 5000)
                        VideoPromoterPerkLog.objects.video_promoter_perk_log_entry(video, promoter, pre_perk, quantity)
                        promoter_pre_perk_obj.decrement_perk_quantity(quantity)
                    else:
                        # Call graph view and return coins won and user graph dictionary till his position
                        (x_data, y_data, coins) = graph.get_pos(total_views + 1)
                        # after retrieving coins again check if can be a bot
                        # Apply post perks
                    if post_perk:
                        if post_perk.perk_id == 1:
                            coins = double_up(post_perk, coins)
                        elif post_perk.perk_id == 2:
                            coins = magnet(post_perk, graph, total_views + 1)
                        VideoPromoterPerkLog.objects.video_promoter_perk_log_entry(video, promoter, post_perk)
                        promoter_post_perk_obj.decrement_perk_quantity()

                    # increment of views
                    video.increment_views_promoter()
                    # local variable
                    total_views += 1

                    # increment in profiling of promoter
                    promoter.promoter_profiling(video, 2)

                    # log entry
                    VideoPromoterLog.objects.promoter_log_entry(video, promoter, ip, share_link, coins, total_views,
                                                                device_type)

                    # Account Entry
                    promoter_account.increment_account_coins(coins)

                    # Video Account Entry
                    video.increment_video_account_expenditure(coins)

                    # Max viewership reached Check
                    if video_account.max_viewership == total_views:
                        video.set_video_inactive()

                    response = JsonResponse({"coins": coins,
                                             "share_link": share_link,
                                             "x_data": x_data,
                                             "y_data": y_data,
                                             "fake_coins": fake_coins,
                                             "status_code": 69})

            activity_meta = {
                "method": "promoter.views.video_viewed",
                "video_uuid": request.POST.get('video_uuid'),
                "video_id": str(video.id),
                "start_time": str(start_time),
                "end_time": str(current_time),
                "watched_time": str(watched_time),
                "video_duration": str(video_duration),
                "coins": str(coins),
                "share_link": str(share_link),
                "x_data": str(x_data),
                "y_data": str(y_data),
                "fake_coins": str(fake_coins),
                "position": str(total_views)
            }
            ActivityLog.objects.create_log(request, "Promoter Video Viewed", activity_meta)
            return response
    else:
        error_meta = {
            "method": "promoter.views.video_viewed",
        }
        ErrorLog.objects.create_log(error_code=35, error_type="Invalid session and Post", error_meta=error_meta,
                                    request=request)
        return JsonResponse({"status_code": 35})


@permission_required('promoter.access_promoter')
def apply_adv_notification(request):
    try:
        user = request.user
        promoter = PromoterProfile.objects.select_related('promoteraccount').get(promoter_id=user)
        promoter_account = promoter.promoteraccount
    except ObjectDoesNotExist:
        error_meta = {
            "method": "promoter.views.apply_adv_notification",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')

    perk = Perks.objects.get_perk_object(5)

    try:
        promoter_perk_obj = promoter_account.promoterperks_set.get(quantity__gt=0, perk_id=perk)
    except PromoterPerks.DoesNotExist:
        error_meta = {
            "method": "promoter.views.apply_adv_notification",
            "perk_id": str(5)
        }
        ErrorLog.objects.create_log(error_code=37, error_type="Promoter Perk Application Error", error_meta=error_meta,
                                    request=request)
        raise SuspiciousOperation("Error Code: 37")

    if not promoter_account.mail_notification_flag:
        promoter_account.mail_notification_flag = 'A'
        promoter_account.save()
        promoter_perk_obj.decrement_perk_quantity()
        perk.increment_times_used()
        activity_meta = {
            "method": "promoter.views.apply_adv_notification",
        }
        ActivityLog.objects.create_log(request, "Promoter apply advance notification perk", activity_meta)
        return HttpResponse("Success")
    else:
        activity_meta = {
            "method": "promoter.views.apply_adv_notification",
        }
        ActivityLog.objects.create_log(request, "Promoter apply advance notification perk", activity_meta)
        return HttpResponse("Already set")


@permission_required('promoter.access_promoter')
def buy_perk(request):
    try:
        user = request.user
        promoter = PromoterProfile.objects.select_related('promoteraccount').get(promoter_id=user)
        promoter_account = promoter.promoteraccount
    except ObjectDoesNotExist:
        error_meta = {
            "method": "promoter.views.buy_perk",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')
    perks = Perks.objects.get_buy_perks(promoter_account)
    context = {
        "perks": perks
    }
    if request.POST and request.POST.get('perk_uuid'):
        perk_uuid = request.POST.get('perk_uuid')
        try:
            perk = Perks.objects.get_perk(perk_uuid)
        except (Perks.DoesNotExist, ValueError):
            error_meta = {
                "method": "promoter.views.buy_perk",
                "perk_uuid": perk_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=6,
                                        error_type="Perk Not exist", error_meta=error_meta)
            raise SuspiciousOperation('ErrorCode: 6')
        if promoter_account.current_eggs < perk.cost:
            error_meta = {
                "method": "promoter.views.buy_perk",
                "perk_id": str(perk.id)
            }
            ErrorLog.objects.create_log(request=request, error_code=36, error_type="Promoter buying not enough eggs",
                                        error_meta=error_meta)
            raise SuspiciousOperation('Error Code: 36')
        else:
            promoter_account.decrement_promoter_eggs(perk.cost)
            log = PerkTransactionLog.objects.perk_transaction_log_entry(promoter, perk)
            promoter_account.increment_promoter_perk(perk)
            activity_meta = {
                "method": "promoter.views.buy_perk",
                "perk_id": str(perk.perk_id),
                "perk_transaction_log_id": str(log.id)

            }
            ActivityLog.objects.create_log(request, "Promoter Perk Transaction", activity_meta)
            context.update({"uuid": log.uuid})
            return render(request, "promoter/buy_perk.html", context)
    else:

        activity_meta = {
            "method": "promoter.views.buy_perk",
        }
        ActivityLog.objects.create_log(request, "Promoter Buy perk", activity_meta)
        return render(request, "promoter/buy_perk.html", context)


@permission_required('promoter.access_promoter')
def promoter_video_watch(request, video_uuid):
    try:
        video = Video.objects.select_related('videofile', 'videoinfo').get_from_uuid(video_uuid)
    except (Video.DoesNotExist, ValueError):
        error_meta = {
            "method": "promoter.views.promoter_video_watch",
            "video_uuid": video_uuid
        }
        ErrorLog.objects.create_log(request=request, error_code=3, error_type="Video Object Error",
                                    error_meta=error_meta)
        raise SuspiciousOperation("Error Code: 3")

    activity_meta = {
        "method": "promoter.views.promoter_video_watch",
        "video_id": str(video.id)
    }
    ActivityLog.objects.create_log(request, "Promoter Watch Video", activity_meta)
    return watch(request, video)


# TODO: collaborate with frontend
@require_POST
@permission_required('promoter.access_promoter')
def promoter_video_abort(request):
    if request.POST.get('video_uuid') and request.POST.get('duration'):
        video_uuid = request.POST.get('video_uuid')
        try:
            video = Video.objects.get_video(video_uuid)
        except (Video.DoesNotExist, ValueError):
            error_meta = {
                "method": "promoter.views.promoter_video_abort",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=3, error_type="Video Object Error",
                                        error_meta=error_meta)
            return JsonResponse({"status_code": 3})
        try:
            promoter = request.user.promoterprofile
        except PromoterProfile.DoesNotExist:
            error_meta = {
                "method": "promoter.views.promoter_video_abort",
            }
            ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
            return JsonResponse({"status_code": 4})

        ip = get_real_ip(request)

        duration = request.POST.get('duration')
        ad_clicked = request.POST.get('ad_clicked', False)
        DurationWatchedLog.objects.duration_watch_log_entry(video, promoter, ip, duration, ad_clicked)
        activity_meta = {
            "method": "promoter.views.promoter_video_abort",
            "duration": str(duration),
            "ad_clicked": str(ad_clicked),
            "video_id": str(video.id)
        }
        ActivityLog.objects.create_log(request, "Promoter Video Abort", activity_meta)
        return JsonResponse({"status_code": 69})
    else:
        error_meta = {
            "method": "promoter.views.promoter_video_abort",
        }
        ErrorLog.objects.create_log(error_code=35, error_type="Invalid session and Post", error_meta=error_meta,
                                    request=request)
        return JsonResponse({"status_code": 35})


@permission_required('promoter.access_promoter')
def survey_home_page(request):
    try:
        promoter = request.user.promoterprofile
    except PromoterProfile.DoesNotExist:
        error_meta = {
            "method": "promoter.views.survey_home_page",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')

    surveys = promoter.survey_profile()

    context = {
        "user": request.user.name,
        "surveys": surveys,
    }
    activity_meta = {
        "method": "promoter.views.survey_home_page",
    }
    ActivityLog.objects.create_log(request, "Promoter Survey Home Page", activity_meta)
    return render(request, 'promoter/survey_home_page.html', context)


@permission_required('promoter.access_promoter')
@transaction.atomic
def survey_filled(request, survey, promoter):
    coins = 0
    if not request.session.get('survey_id', None):
        error_meta = {
            "method": "promoter.views.survey_filled",
        }
        ErrorLog.objects.create_log(error_code=35, error_type="Invalid session and Post", error_meta=error_meta,
                                    request=request)
        raise SuspiciousOperation('Error Code: 35')
    else:
        survey_id = int(request.session.pop('survey_id'))
        if survey_id != survey.id or not survey_id:
            error_meta = {
                "method": "promoter.views.survey_filled",
                "survey_id": str(survey.id),
                "session_survey_id": str(survey_id)
            }
            ErrorLog.objects.create_log(error_code=38, error_type="Survey session data inconsistent",
                                        error_meta=error_meta,
                                        request=request)
            raise SuspiciousOperation('Error Code: 38')
        else:
            if promoter.check_survey_filled(survey):
                activity_meta = {
                    "method": "promoter.views.survey_filled",
                    "survey_id": str(survey.id)
                }
                ActivityLog.objects.create_log(request, "Promoter Survey Filled Again", activity_meta)
            else:
                promoter_account = promoter.promoteraccount
                ip = get_real_ip(request)
                device_type = "C"
                survey_account = survey.surveyaccount
                survey_insights = survey.surveyinsights
                total_fills = survey_insights.total_fills()

                if survey_account.max_fill <= total_fills or not survey.active:
                    survey.increment_fill_promoter()
                    total_fills += 1
                    promoter.promoter_profiling(survey, 4)
                    SurveyPromoterLog.objects.promoter_survey_log_entry(survey, promoter, ip, coins, total_fills,
                                                                        device_type)
                    activity_meta = {
                        "method": "promoter.views.survey_filled",
                        "survey_id": str(survey.id),
                        "position": str(total_fills)
                    }
                    ActivityLog.objects.create_log(request, "Promoter Survey fill after inactive", activity_meta)
                    return HttpResponse("Sorry yaar thoda sa reh gyaa! next time Pakka")
                else:
                    graph = survey_account.graph_id

                    (x_data, y_data, coins) = graph.get_pos(total_fills + 1)

                    survey.increment_fill_promoter()

                    total_fills += 1

                    promoter.promoter_profiling(survey, 4)

                    SurveyPromoterLog.objects.promoter_survey_log_entry(survey, promoter, ip, coins, total_fills,
                                                                        device_type)

                    promoter_account.increment_account_coins(coins)

                    survey.increment_survey_account_expenditure(coins)

                    if survey_account.max_fill == total_fills:
                        survey.set_survey_inactive()

                    request.session['coins'] = coins
                    request.session['x_data'] = x_data
                    request.session['y_data'] = y_data

                    activity_meta = {
                        "method": "promoter.views.survey_filled",
                        "survey_id": str(survey.id),
                        "position": str(total_fills),
                        "coins": str(coins),
                        "x_data": str(x_data),
                        "y_data": str(y_data)
                    }
                    ActivityLog.objects.create_log(request, "Promoter Survey Filled", activity_meta)
                    return redirect('/pr/survey/completed/')


@permission_required('promoter.access_promoter')
def survey_complete(request):
    coins = request.session.pop('coins', 0)
    x_data = request.session.pop('x_data', -1)
    y_data = request.session.pop('y_data', -1)

    context = {
        "coins": coins,
        "x_data": x_data,
        "y_data": y_data
    }
    activity_meta = {
        "method": "promoter.views.survey_complete"
    }
    ActivityLog.objects.create_log(request, "Survey Complete Display Page", activity_meta)
    return render(request, "promoter/survey_completed.html", context)


@permission_required('promoter.access_promoter')
def fill_survey_v2(request, survey_uuid):
    try:
        promoter = request.user.promoterprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "promoter.views.fill_survey_v2",
        }
        ErrorLog.objects.create_log(4, "Promoter Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 4')
    try:
        survey = Survey.objects.get_survey(survey_uuid)
    except (Survey.DoesNotExist, ValueError):
        error_meta = {
            "method": "promoter.views.fill_survey_v2",
            "survey_uuid": survey_uuid
        }
        ErrorLog.objects.create_log(request=request, error_code=7, error_type="Survey Object Error",
                                    error_meta=error_meta)
        raise SuspiciousOperation('Error Code: 7')

    if promoter.check_survey_filled(survey):
        activity_meta = {
            "method": "promoter.views.fill_survey_v2",
            "survey_id": str(survey.id)
        }
        ActivityLog.objects.create_log(request, "Promoter Survey Filling Again", activity_meta)
        return HttpResponse("already Filled")
    else:
        total_questionset = request.session.get('total_questionset', None)
        question_set_number = request.session.get('question_set_number', None)

        if request.session.get('survey_id', None):
            survey_id = int(request.session['survey_id'])
            if survey_id != survey.id:
                request.session['survey_id'] = survey.id
                total_questionset = None
                question_set_number = None
        else:
            request.session['survey_id'] = survey.id

        if request.POST:
            questionset = survey.questionset_set.all().order_by('sort_id')[question_set_number - 1]
            question_set_answer_form = QuestionSetAnswerForm(request.POST, questionset=questionset, promoter=promoter)
            if question_set_answer_form.is_valid():
                questions = questionset.question_set.all().order_by('sort_id')
                for question in questions:
                    answer_text = question_set_answer_form.cleaned_data.get('ques-' + str(question.id) + '-answer',
                                                                            None)
                    try:
                        answer_obj = Answer.objects.get(question_id=question, promoter_id=promoter)
                    except Answer.DoesNotExist:
                        answer_obj = None

                    if answer_obj:
                        answer_obj_parsed = json.loads(answer_obj.answer_text)
                        if question.question_type == 'CH2' or question.question_type == 'CH6':
                            comment = question_set_answer_form.cleaned_data.get('ques-' + str(question.id) + '-comment',
                                                                                None)

                            if str(answer_obj_parsed['text']) != str(answer_text) or str(
                                    answer_obj_parsed['comment']) != str(comment):
                                answer_dict = {
                                    "text": answer_text,
                                    "comment": comment
                                }
                                answer_obj.answer_text = json.dumps(answer_dict)
                                answer_obj.save()
                        else:
                            if str(answer_obj_parsed['text']) != str(answer_text):
                                answer_dict = {
                                    "text": answer_text
                                }
                                answer_obj.answer_text = json.dumps(answer_dict)
                                answer_obj.save()
                    else:

                        if question.question_type == 'CH2' or question.question_type == 'CH6':
                            comment = question_set_answer_form.cleaned_data.get('ques-' + str(question.id) + '-comment',
                                                                                None)
                            answer_dict = {
                                "text": answer_text,
                                "comment": comment
                            }
                        else:
                            answer_dict = {
                                "text": answer_text
                            }
                        answer_str = json.dumps(answer_dict)
                        answer_obj = Answer(question_id=question, promoter_id=promoter, answer_text=answer_str)
                        answer_obj.save()

                if question_set_number == total_questionset:
                    request.session.pop('total_questionset')
                    request.session.pop('question_set_number')
                    return survey_filled(request, survey, promoter)
                else:
                    request.session['question_set_number'] += 1
                    activity_meta = {
                        "method": "promoter.views.fill_survey_v2",
                        "survey_id": str(survey.id),
                        "total_questionset": str(total_questionset),
                        "question_set_number": str(question_set_number)
                    }
                    ActivityLog.objects.create_log(request, "Promoter Survey Question Filled", activity_meta)
                    return redirect('/pr/fill_survey/' + str(survey.uuid))
            else:
                context = {
                    "questionset": questionset,
                    "question_set_answer_form": question_set_answer_form
                }
                return render(request, 'promoter/fill_survey_v2.html', context)
        else:
            if not total_questionset or not question_set_number:
                questionset = survey.questionset_set.all().order_by('sort_id').first()
                total_questionset = survey.questionset_set.all().count()
                question_set_number = 1
                request.session['question_set_number'] = question_set_number
                request.session['total_questionset'] = total_questionset
            else:
                questionset = survey.questionset_set.all().order_by('sort_id')[question_set_number - 1]

            question_set_answer_form = QuestionSetAnswerForm(questionset=questionset, promoter=promoter)
            context = {
                "questionset": questionset,
                "question_set_answer_form": question_set_answer_form
            }
            activity_meta = {
                "method": "promoter.views.fill_survey_v2",
                "survey_id": str(survey.id),
                "total_questionset": str(total_questionset),
                "question_set_number": str(question_set_number)
            }
            ActivityLog.objects.create_log(request, "Promoter Survey Display Question", activity_meta)
            return render(request, 'promoter/fill_survey_v2.html', context)


@permission_required('promoter.access_promoter')
def back_questionset(request):
    question_set_number = request.session.get('question_set_number')
    if question_set_number:
        if question_set_number > 1:
            question_set_number -= 1
        else:
            question_set_number = 1
        request.session['question_set_number'] = question_set_number
        activity_meta = {
            "method": "promoter.views.back_questionset",
            "question_set_number": question_set_number
        }
        ActivityLog.objects.create_log(request, "Promoter Back Question Set", activity_meta)
        return JsonResponse({"redirect": True})
    else:
        return JsonResponse({"redirect": False})


def delete_promoter(request):
    # TODO: Add additional related tasks
    request.user.set_user_inactive()
    logout(request)
    return HttpResponse("Account deactivated")


@permission_required('promoter.access_promoter')  # FIXME
def filled(request):
    promoter = request.user.promoterprofile
    logs = promoter.surveypromoterlog_set.all().order_by('create_time')

    context = {
        "logs": logs
    }
    return render(request, 'promoter/survey_filled.html', context)
