import time

from django.http import JsonResponse
from ipware.ip import get_real_ip
from admin_custom.views_2 import log_error, log_activity
from logs.models import VideoUnsubscribedLog
from promoter.models import PromoterProfile
from video.models import Video

""" 'A' --> abort
'C' --> Charge Client
'B' --> Backlink API
'V' --> End of Video"""


def abort_handler(request):
    return main_handler(request, 'A')


def eov_handler(request):
    return main_handler(request, 'V')


def at_10_sec(request):
    return main_handler(request, 'C')


def at_30_sec(request):
    return main_handler(request, 'B')


def main_handler(request, parent):
    if request.user.is_authenticated():
        return JsonResponse({"status_code": 74})
    else:
        try:
            video_uuid = request.POST.get('video_uuid')
            video_id = request.session.get('video_id')
            if not video_uuid or not video_id:
                raise AssertionError
            try:
                video = Video.objects.get_video(video_uuid)
            except Video.DoesNotExist:
                error_meta = {
                    "method": "user_login.views.charge_client",
                    "video_uuid": video_uuid
                }
                log_error(request, 74, "ObjectDoesNotExist", error_meta)
                return JsonResponse({"status_code": 74})
            except ValueError:
                error_meta = {
                    "method": "user_login.views.charge_client",
                    "video_uuid": video_uuid
                }
                log_error(request, 75, "ValueError", error_meta)
                return JsonResponse({"status_code": 75})
            if video.id != video_id:
                raise KeyError
        except AssertionError:
            error_meta = {
                    "method": "user_login.views.main_method", "parent": str(parent)
                }
            log_error(request, 77, "NoPost", error_meta)
            return JsonResponse({"status_code": 77})
        except KeyError:
            error_meta = {
                    "method": "user_login.views.main_method", "parent": str(parent)
                }
            log_error(request, 77, "keys do not match", error_meta)
            return JsonResponse({"status_code": 77})

        else:
            start_time = request.session.pop('start_time', None)
            current_time = time.time()

            duration = request.POST.get('duration')
            ad_clicked = request.POST.get('ad_clicked')
            video_duration = float(request.session.pop('video_duration', None))
            watched_time = current_time - start_time
            
            promoter_uuid = request.session.pop('promoter_uuid', None)
            
            device_type = None
            ip = get_real_ip(request)
            
            promoter = None
            if promoter_uuid is not None:
                try:
                    promoter = PromoterProfile.objects.get_promoter(promoter_uuid)
                except PromoterProfile.DoesNotExist:
                    error_meta = {
                        "method": "user_login.views.viewed",
                        "promoter_uuid": promoter_uuid
                    }
                    log_error(request, 76, "ObjectDoesNotExist", error_meta)
                    promoter = None
                except ValueError:
                    error_meta = {
                        "method": "user_login.views.viewed",
                        "promoter_uuid": promoter_uuid
                    }
                    log_error(request, 75, "ValueError", error_meta)
                    promoter = None

            # Security checks
            security_flag = security_check(watched_time, duration, video_duration)
            if security_flag:
                if parent is 'C':
                    response_dict, total_views = charge_client(request, video, promoter, promoter_uuid, duration,
                                                               ip)
                    # Log Entry
                    log = VideoUnsubscribedLog.objects.unsubsribed_log_entry(video, total_views, duration, promoter, ip,
                                                                             device_type, ad_clicked)
                    request.session['video_unsubscribed_log_id'] = log.id
                    return JsonResponse(response_dict)
                elif parent is 'B':
                    if promoter:
                        response_dict = backlink_viewed(request, video, promoter)
                        return JsonResponse(response_dict)
                    else:
                        error_meta = {
                            "method": "user_login.views.backlink_viewed",
                        }
                        log_error(request, 77, "NoPost", error_meta)
                        return JsonResponse({"status_code": 77})
                
                elif parent is 'A':
                    create_flag, client_flag = judge_abort(video_duration, ad_clicked, duration)
                    if create_flag and client_flag:
                        response_dict, total_views = charge_client(request, video, promoter, promoter_uuid, duration,
                                                                   ip)
                        # Log Entry
                        VideoUnsubscribedLog.objects.unsubsribed_log_entry(video, total_views, duration, promoter, ip,
                                                                           device_type, ad_clicked)
                        if ad_clicked:
                            response_dict.update({"redirect": True})
                        return JsonResponse(response_dict)
                    elif create_flag and not client_flag:
                        if ad_clicked:
                            response_dict = {"redirect": True, "status_code": 69}
                        else:
                            response_dict = {"status_code": 69}
                        VideoUnsubscribedLog.objects.create(video_id=video, duration=duration, promoter_id=promoter,
                                                            ip=ip, device_type=device_type, ad_clicked=ad_clicked)
                        return JsonResponse(response_dict)
                    elif not create_flag:
                        return update_log_entry(request, duration, ad_clicked)

                elif parent is 'V':
                    client_flag, promoter_flag = viewed(video_duration)
                    if client_flag and promoter_flag:
                        response_dict, total_views = charge_client(request, video, promoter, promoter_uuid, duration,
                                                                   ip)
                        # Log Entry
                        VideoUnsubscribedLog.objects.unsubsribed_log_entry(video, total_views, duration, promoter, ip,
                                                                           device_type, ad_clicked)
                        backlink_viewed(request, video, promoter)
                        if ad_clicked:
                            response_dict.update({"redirect": True})
                        return JsonResponse(response_dict)
                    elif not client_flag and promoter_flag:
                        response_dict = backlink_viewed(request, video, promoter)
                        if ad_clicked:
                            response_dict.update({"redirect": True})
                        return JsonResponse(response_dict)
                    else:
                        return update_log_entry(request, duration, False)

            else:
                error_meta = {
                        "method": "user_login.views.main_method", "parent": str(parent)
                    }
                log_error(request, 77, "Security failed", error_meta)
                return JsonResponse({"status_code": 77})


def judge_abort(video_duration, ad_clicked, duration):
    time_marker1 = 10.0
    time_marker2 = 30.0
    client_flag = False
    create_flag = False

    if video_duration <= time_marker1:
        create_flag = True
        if ad_clicked:
            client_flag = True
        # else:
        #     client_flag = False

    elif time_marker1 < video_duration <= time_marker2:
        if duration <= time_marker1:
            create_flag = True
            if ad_clicked:
                client_flag = True
            # else:
            #     client_flag = False
        # elif time_marker1 < duration < video_duration:
        #     if ad_clicked:
        #         client_flag = True
        #     else:
        #         client_flag = True
        
    elif video_duration > time_marker2:
        if duration <= time_marker1:
            create_flag = True
            if ad_clicked:
                client_flag = True
            # else:
            #     client_flag = False
        # elif time_marker1 < duration < video_duration:
        #     if ad_clicked:
        #         client_flag = True
        #     else:
        #         client_flag = True
        # elif time_marker2 <= duration < video_duration:
        #     if ad_clicked:
        #         client_flag = True
        #     else:
        #         client_flag = True
    
    return create_flag, client_flag


def viewed(video_duration):
    time_marker1 = 10.0
    time_marker2 = 30.0
    client_flag = False
    promoter_flag = False
    
    if video_duration <= time_marker1:
        client_flag = True
        promoter_flag = True
    elif time_marker1 < video_duration <= time_marker2:
        promoter_flag = True
        
    return client_flag, promoter_flag
    

def charge_client(request, video, promoter, promoter_uuid, duration, watched_time):
    video_insights = video.videoinsights
    video_account = video.videoaccount

    total_views = video_insights.total_views()
    activity_meta = {
        "method": "user_login.views.charge_client",
        "video_id": video.id,
        "watched_time": watched_time,
        "duration_watched": duration
    }
    if promoter is not None:
        share_link = '/watch/{0}/{1}'.format(video.slug, promoter_uuid)
        activity_meta.update({"promoter_id": promoter.id})
    else:
        share_link = '/watch/{0}'.format(video.slug)

    # increment of views
    video.increment_views_anonymous_viewers()
    # local variable
    total_views += 1

    # Max viewership reached Check
    if video_account.max_viewership == total_views:
        video.set_video_inactive()

    log_activity(request, "Video Viewed - Charge Client", activity_meta)
    
    response_dict = {"share_link": share_link, "status_code": 69}
    return response_dict, total_views


def backlink_viewed(request, video, promoter):
    video_account = video.videoaccount
    video_insights = video.videoinsights
    total_views = video_insights.total_views()
    if video.active is True and video_account.max_viewership >= total_views:
        video.increment_insights_backlinks()
        promoter.promoter_backlink(video)

    response_dict = {"status_code": 69}
    activity_meta = {
        "method": "user_login.views.backlink_viewed",
        "video_id": video.id,
        "promoter_id": promoter.id
    }
    log_activity(request, "Video Viewed - Backlink", activity_meta)
    return response_dict


def security_check(watched_time, duration, video_duration):
    if watched_time < duration:
        return False
    elif duration > video_duration:
        return False
    else:
        return True


def update_log_entry(request, duration, ad_clicked):
    log_id = request.session.pop('video_unsubscribed_log_id')
    if log_id is None:
        error_meta = {
            "method": "user_login.views.abort_after_10",
            "log_id": log_id
        }
        log_error(request, 74, "ObjectDoesNotExist", error_meta)
        return JsonResponse({"status_code": 74})
    else:
        try:
            log = VideoUnsubscribedLog.objects.get(id=log_id)
        except VideoUnsubscribedLog.DoesNotExist:
            error_meta = {
                "method": "user_login.views.abort_after_10",
                "log_id": log_id
            }
            log_error(request, 74, "ObjectDoesNotExist", error_meta)
            return JsonResponse({"status_code": 74})
        
        log.duration = duration
        if ad_clicked:
            log.ad_clicked = ad_clicked
            log.save()
            return JsonResponse({"redirect": True, "status_code": 69})
        else:
            log.save()
            return JsonResponse({"status_code": 69})
