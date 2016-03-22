from models import ErrorLog, ActivityLog, VideoCompletionLog, SurveyCompletionLog
from ipware.ip import get_real_ip
from django.http import JsonResponse


def log_error(request, error_code, error_type, error_meta):
    if request:
        if request.user.is_authenticated():
            ErrorLog.objects.create(error_code=error_code, error_type=error_type, error_meta=error_meta,
                                    actor=request.user, actor_ip=get_real_ip(request))
        else:
            ErrorLog.objects.create(error_code=error_code, error_type=error_type, error_meta=error_meta,
                                    actor_ip=get_real_ip(request))
    else:
        ErrorLog.objects.create(error_code=error_code, error_type=error_type, error_meta=error_meta,
                                actor_ip=None)


def log_activity(request, action_type, act_meta):
    if request.user.is_authenticated():
        ActivityLog.objects.create(actor=request.user, actor_ip=get_real_ip(request),
                                   action_type=action_type, act_meta=act_meta)
    else:
        ActivityLog.objects.create(actor_ip=get_real_ip(request),
                                   action_type=action_type, act_meta=act_meta)


def video_verified(video, status, false_views=0):
    completion_log = video.videocompletionlog_set.order_by('-create_time')[0]
    completion_log.verified = status
    completion_log.false_views = false_views
    completion_log.save()


def set_browser_fingerprint(request):
    BF = request.GET.get('BF', None)
    if BF:
        request.session['fingerprint'] = BF
    return JsonResponse({})
