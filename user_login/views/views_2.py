from django.shortcuts import redirect
from video.views import \
    watch
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist
from ipware.ip import get_real_ip
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST, require_GET
from video.models import Video
from logs.models import VideoUnsubscribedLog
import time
from promoter.models import PromoterProfile
import json
from admin_custom.models import ErrorLog, ActivityLog
from django.core.exceptions import SuspiciousOperation


@require_GET
def redirection(request):
    if request.user.is_authenticated():
        error_meta = {
            "method": "user_login.views.redirection",
        }
        ErrorLog.objects.create_log(102, "Authenticated User in redirection", error_meta, request)
        return redirect('/')
    elif not request.GET.get('link') or not request.GET.get('video_uuid'):
        error_meta = {
            "method": "user_login.views.redirection",
        }
        ErrorLog.objects.create_log(request=request, error_code=1, error_type="NoGet", error_meta=error_meta)
        raise SuspiciousOperation('Error Code: 1')
    else:
        link = request.GET.get('link')
        video_uuid = request.GET.get('video_uuid')
        try:
            video = Video.objects.get_video(video_uuid)
        except (Video.ObjectDoesNotExist, ValueError):
            error_meta = {
                "method": "user_login.views.redirection",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=3, error_type="Video Object Error",
                                        error_meta=error_meta)
            return HttpResponseNotFound('<h1>Page not found</h1>'
                                        'Error Code: 3')

        # Increment Video Insights
        video.increment_insights_redirection_click()

        activity_meta = {
            "method": "user_login.views.redirection",
            "link": request.GET.get('link'),
            "video_uuid": request.GET.get('video_uuid')
        }
        ActivityLog.objects.create_log(request=request, action_type="Redirection",
                                       act_meta=activity_meta)
        return redirect(link)


# TODO: Remove this method after charge client and backlink_viewed methods are implemented
@transaction.atomic
@require_POST
def viewed(request):
    if request.user.is_authenticated():
        return JsonResponse({"status_code": 81})
    elif request.POST.get('video_uuid') and request.session.get('video_id'):
        promoter = None
        video_uuid = request.POST.get('video_uuid')
        try:
            video = Video.objects.get_video(video_uuid)
        except ObjectDoesNotExist:
            error_meta = {
                "method": "user_login.views.viewed",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 74})
        except ValueError:
            error_meta = {
                "method": "user_login.views.viewed",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 75})

        video_id = request.session.pop('video_id', None)
        video_duration = float(request.session.pop('video_duration', None))
        start_time = request.session.pop('start_time', None)
        current_time = time.time()

        watched_time = current_time - start_time

        if video.id != video_id:
            return HttpResponseBadRequest("Bad Boy")
        else:

            # promoter_uuid = request.POST.get('promoter_uuid')
            promoter_uuid = request.session.pop('promoter_uuid', None)
            # todo: Receive from frontend
            duration = request.POST.get('duration')
            # ad_clicked = request.POST.get('ad_clicked')
            ad_clicked = False

            device_type = None
            video_insights = video.videoinsights
            video_account = video.videoaccount
            total_views = video_insights.total_views()
            share_link = '/watch/{0}'.format(video.slug)

            ip = get_real_ip(request)

            if promoter_uuid is not None:
                try:
                    promoter = PromoterProfile.objects.get_promoter(promoter_uuid)
                except ObjectDoesNotExist:
                    error_meta = {
                        "method": "user_login.views.viewed",
                        "promoter_uuid": promoter_uuid
                    }
                    ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet",
                                                error_meta=error_meta)
                    promoter = None
                except ValueError:
                    error_meta = {
                        "method": "user_login.views.viewed",
                        "promoter_uuid": promoter_uuid
                    }
                    ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet",
                                                error_meta=error_meta)
                    promoter = None

            if video.active is True and video_account.max_viewership >= total_views:
                if promoter is not None:
                    video.increment_insights_backlinks()
                    promoter.promoter_backlink(video)
                    share_link = '/watch/{0}/{1}'.format(video.slug, promoter_uuid)
                else:
                    share_link = '/watch/{0}'.format(video.slug)

            # increment of views
            video.increment_views_anonymous_viewers()
            # local variable
            total_views += 1

            # Log Entry
            VideoUnsubscribedLog.objects.unsubsribed_log_entry(video, total_views, int(watched_time), promoter, ip,
                                                               device_type, ad_clicked)

            # Max viewership reached Check
            if video_account.max_viewership == total_views:
                video.set_video_inactive()

            response = JsonResponse({"share_link": share_link, "status_code": 69})
            activity_meta = {
                "method": "user_login.views.viewed",
                "video_uuid": video_uuid,
                "promoter_uuid": promoter_uuid,
                "watched_time": str(watched_time),
                "duration_watched": duration
            }
            ActivityLog.objects.create_log(request=request, action_type="Video Viewed",
                                           act_meta=activity_meta)
            return response
    else:
        error_meta = {
            "method": "user_login.views.viewed",
        }
        ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
        return JsonResponse({"status_code": 77})


def anonymous_video_watch(request, slug, promoter_uuid=None):
    try:
        video = Video.objects.get_video_from_slug(slug)
    except (Video.DoesNotExist, ValueError):
        error_meta = {
            "method": "user_login.views.anonymous_video_watch",
            "video_slug": slug
        }
        ErrorLog.objects.create_log(request=request, error_code=3, error_type="Video Object Error",
                                    error_meta=error_meta)
        return HttpResponseNotFound('<h1>Page Not Found</h1>'
                                    'Error Code: 3')

    if request.user.is_authenticated():
        user_type = request.user.get_user_type()
        if user_type == 'P':
            return redirect('/pr/watch/{0}/'.format(video.uuid))
        else:
            return redirect('/')
    else:
        activity_meta = {
            "method": "user_login.views.anonymous_video_watch",
            "video_slug": slug,
            "promoter_uuid": promoter_uuid
        }
        ActivityLog.objects.create_log(request=request, action_type="Native Watch Video",
                                       act_meta=activity_meta)
        return watch(request, video, promoter_uuid)


@transaction.atomic
@require_POST
def charge_client(request):
    if request.user.is_authenticated():
        return JsonResponse({"status_code": 74})
    elif request.POST.get('video_uuid') and request.session.get('video_id'):
        video_uuid = request.POST.get('video_uuid')
        promoter = None
        try:
            video = Video.objects.get_video(video_uuid)
        except ObjectDoesNotExist:
            error_meta = {
                "method": "user_login.views.charge_client",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 74})
        except ValueError:
            error_meta = {
                "method": "user_login.views.charge_client",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 75})

        video_id = request.session.pop('video_id', None)
        video_duration = float(request.session.pop('video_duration', None))
        start_time = request.session.pop('start_time', None)
        current_time = time.time()
        ad_clicked = request.POST.get('ad_clicked')
        # todo: Receive from frontend
        duration = request.POST.get('duration')

        watched_time = current_time - start_time

        # todo: duration and watched time checks
        # todo: video-duration if less than 10 check
        if video.id != video_id or not check_watch_arguments(watched_time, duration, ad_clicked, video_duration):
            return HttpResponseBadRequest("Bad Boy")
        else:
            # promoter_uuid = request.POST.get('promoter_uuid')
            promoter_uuid = request.session.pop('promoter_uuid', None)

            video_insights = video.videoinsights
            video_account = video.videoaccount

            device_type = None
            total_views = video_insights.total_views()
            share_link = '/watch/{0}'.format(video.slug)

            ip = get_real_ip(request)

            if promoter_uuid is not None:
                try:
                    promoter = PromoterProfile.objects.get_promoter(promoter_uuid)
                except ObjectDoesNotExist:
                    error_meta = {
                        "method": "user_login.views.charge_client",
                        "promoter_uuid": promoter_uuid
                    }
                    ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet",
                                                error_meta=error_meta)
                    promoter = None
                except ValueError:
                    error_meta = {
                        "method": "user_login.views.charge_client",
                        "promoter_uuid": promoter_uuid
                    }
                    ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet",
                                                error_meta=error_meta)
                    promoter = None

            if promoter is not None:
                share_link = '/watch/{0}/{1}'.format(video.slug, promoter_uuid)
            else:
                share_link = '/watch/{0}'.format(video.slug)

            # increment of views
            video.increment_views_anonymous_viewers()
            # local variable
            total_views += 1

            # Log Entry
            log = VideoUnsubscribedLog.objects.unsubsribed_log_entry(video, total_views, duration, promoter, ip,
                                                                     device_type, ad_clicked)

            # Max viewership reached Check
            if video_account.max_viewership == total_views:
                video.set_video_inactive()

            # session entry
            if (watched_time < 10 or duration < 10) and ad_clicked:
                # todo redirect here 2 ways: 1- frontend 2- backend
                return JsonResponse({"redirect": True, "status_code": 69})
            else:
                request.session['video_unsubscribed_log_id'] = log.id

            response = JsonResponse({"share_link": share_link, "status_code": 69})
            activity_meta = {
                "method": "user_login.views.charge_client",
                "video_uuid": video_uuid,
                "promoter_uuid": promoter_uuid,
                "watched_time": watched_time,
                "duration_watched": duration
            }
            ActivityLog.objects.create_log(request=request, action_type="Video viewed - Charge client",
                                           act_meta=activity_meta)
            return response
    else:
        error_meta = {
            "method": "user_login.views.charge_client",
        }
        ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
        return JsonResponse({"status_code": 77})


@transaction.atomic
@require_POST
def backlink_viewed(request):
    if request.POST.get('video_uuid') and request.POST.get('promoter_uuid'):
        video_uuid = request.POST.get('video_uuid')
        promoter_uuid = request.POST.get('promoter_uuid')

        try:
            video = Video.objects.get_video(video_uuid)
            video_account = video.videoaccount
            video_insights = video.videoinsights
        except ObjectDoesNotExist:
            error_meta = {
                "method": "user_login.views.backlink_viewed",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 74})
        except ValueError:
            error_meta = {
                "method": "user_login.views.backlink_viewed",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 75})

        total_views = video_insights.total_views()
        share_link = '/watch/{0}'.format(video.slug)

        try:
            promoter = PromoterProfile.objects.get_promoter(promoter_uuid)
        except ObjectDoesNotExist:
            error_meta = {
                "method": "user_login.views.backlink_viewed",
                "promoter_uuid": promoter_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            promoter = None
        except ValueError:
            error_meta = {
                "method": "user_login.views.backlink_viewed",
                "promoter_uuid": promoter_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            promoter = None

        if video.active is True and video_account.max_viewership >= total_views:
            if promoter is not None:
                video.increment_insights_backlinks()
                promoter.promoter_backlink(video)
                share_link = '/watch/{0}/{1}'.format(video.slug, promoter_uuid)
            else:
                share_link = '/watch/{0}'.format(video.slug)
        response = JsonResponse({"share_link": share_link, "status_code": 69})
        activity_meta = {
            "method": "user_login.views.backlink_viewed",
            "video_uuid": request.POST.get('video_uuid'),
            "promoter_uuid": request.POST.get('promoter_uuid')
        }
        ActivityLog.objects.create_log(request=request, action_type="Video Viewed -Backlink",
                                       act_meta=activity_meta)
        return response
    else:
        error_meta = {
            "method": "user_login.views.backlink_viewed",
        }
        ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
        return JsonResponse({"status_code": 77})


def abort_handler(request):
    if request.user.is_authenticated():
        return JsonResponse({"status_code": 74})
    else:
        duration = float(request.POST.get('duration'))
        ad_clicked = request.POST.get('ad_clicked')

        if duration < 10:
            if ad_clicked:
                return charge_client(request)
            else:
                return abort_before_10(request)

        else:
            return abort_after_10(request)


def abort_before_10(request):
    if request.POST.get('video_uuid') and request.session.get('video_id'):
        video_uuid = request.POST.get('video_uuid')
        promoter = None
        duration = float(request.POST.get('duration'))
        ad_clicked = request.POST.get('ad_clicked')

        try:
            video = Video.objects.get_video(video_uuid)
        except ObjectDoesNotExist:
            error_meta = {
                "method": "user_login.views.abort_before_10",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 74})
        except ValueError:
            error_meta = {
                "method": "user_login.views.abort_before_10",
                "video_uuid": video_uuid
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 75})

        video_id = request.session.pop('video_id', None)
        promoter_uuid = request.session.pop('promoter_uuid', None)
        video_duration = float(request.session.pop('video_duration', None))
        start_time = request.session.pop('start_time', None)
        current_time = time.time()

        watched_time = current_time - start_time

        ip = get_real_ip(request)

        device_type = None

        # todo: use watched time and duration checks
        if video.id != video_id:
            return HttpResponseBadRequest("Bad Boy")
        else:
            if promoter_uuid is not None:
                try:
                    promoter = PromoterProfile.objects.get_promoter(promoter_uuid)
                except ObjectDoesNotExist:
                    error_meta = {
                        "method": "user_login.views.charge_client",
                        "promoter_uuid": promoter_uuid
                    }
                    ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet",
                                                error_meta=error_meta)
                    promoter = None
                except ValueError:
                    error_meta = {
                        "method": "user_login.views.charge_client",
                        "promoter_uuid": promoter_uuid
                    }
                    ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet",
                                                error_meta=error_meta)
                    promoter = None

            VideoUnsubscribedLog.objects.create(video_id=video, duration=duration, promoter_id=promoter, ip=ip,
                                                device_type=device_type, ad_clicked=ad_clicked)

            return JsonResponse({"status_code": 69})
    else:
        error_meta = {
            "method": "user_login.views.abort_before_10",
        }
        ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
        return JsonResponse({"status_code": 77})


def abort_after_10(request):
    if request.POST.get('duration') and request.session.get('video_unsubscribed_log_id'):
        duration = float(request.POST.get('duration'))
        ad_clicked = request.POST.get('ad_clicked')
        log_id = request.session.pop('video_unsubscribed_log_id')
        try:
            log = VideoUnsubscribedLog.objects.get(id=log_id)
        except ObjectDoesNotExist:
            error_meta = {
                "method": "user_login.views.abort_after_10",
                "log_id": log_id
            }
            ErrorLog.objects.create_log(request=request, error_code=73, error_type="NoGet", error_meta=error_meta)
            return JsonResponse({"status_code": 74})
        except ValueError:
            error_meta = {
                "method": "user_login.views.abort_after_10",
                "log_id": log_id
            }

            return JsonResponse({"status_code": 75})

        log.duration = duration
        if ad_clicked:
            log.ad_clicked = ad_clicked
            log.save()
            return JsonResponse({"redirect": True, "status_code": 69})
        else:
            log.save()
            return JsonResponse({"status_code": 69})
    else:
        error_meta = {
            "method": "user_login.views.abort_after_10",
        }
        return JsonResponse({"status_code": 77})


def viewed_handler(request):
    if request.user.is_authenticated():
        return JsonResponse({"status_code": 74})
    else:
        video_duration = float(request.session.get('video_duration'))
        duration = float(request.POST.get('duration'))
        ad_clicked = request.POST.get('ad_clicked')

        if video_duration < 10:
            charge_client_response = charge_client(request)
            charge_client_dict = json.loads(charge_client_response)
            if charge_client_dict['status_code'] == 69:
                backlink_viewed_response = backlink_viewed(request)
                backlink_viewed_dict = json.loads(backlink_viewed_response)
                if backlink_viewed_dict['status_code'] == 69:
                    return charge_client_response
                else:
                    return backlink_viewed_response
            else:
                return charge_client_response
        elif video_duration < 30:
            backlink_viewed_response = backlink_viewed(request)
            backlink_viewed_dict = json.loads(backlink_viewed_response)
            if backlink_viewed_dict['status_code'] == 69:
                abort_after_10_response = abort_after_10(request)
                abort_after_10_dict = json.loads(abort_after_10_response)
                if abort_after_10_dict['status_code'] == 69:
                    return backlink_viewed_response
                else:
                    return abort_after_10_response
            else:
                return backlink_viewed_response
        else:
            return abort_after_10(request)


def check_watch_arguments(watched_time, duration, ad_clicked, video_duration):
    if video_duration < 10:
        if watched_time < video_duration and duration < video_duration:
            if ad_clicked:
                return True
            else:
                return False
        else:
            return True
    else:
        if watched_time < 10 and duration < 10:
            if ad_clicked:
                return True
            else:
                return False
        return True
