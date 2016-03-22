from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render
from admin_custom.models import ErrorLog
from survey.models import Survey, SurveyState
from video.models import Video, VideoState

# Create your views here.


def success_video(request, video_uuid):
    video = Video.objects.get_video(video_uuid)
    try:
        previous_state = video.get_previous_state()
    except VideoState.DoesNotExist:
        error_meta = {
            "method": "client_transaction.views.success_video",
            "video_uuid": video_uuid,
        }
        ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 51')
    else:
        if previous_state.current in ['IF', 'EP']:
            if video.parent_video is None:
                video.create_state(previous_state, 'PA')
            else:
                video.create_state(previous_state, 'VU')
            context = {
                'video_uuid': video_uuid
            }
            return render(request, 'client/success.html', context)
        else:
            error_meta = {
                "method": "client_transaction.views.success_video",
                "video_uuid": video_uuid,
                "previous_state_id": str(previous_state.id)
            }
            ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
            raise SuspiciousOperation('Error Code: 51')


def success_survey(request, survey_uuid):
    survey = Survey.objects.get_survey(survey_uuid)
    try:
        previous_state = survey.get_previous_state()
    except SurveyState.DoesNotExist:
        error_meta = {
            "method": "client_transaction.views.success_survey",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')
    else:
        if previous_state.current in ['IF', 'EP']:
            if survey.parent_survey is None:
                survey.create_state(previous_state, 'PA')
            else:
                survey.create_state(previous_state, 'SF')
            context = {
                'survey_uuid': survey_uuid
            }
            return render(request, 'client/success.html', context)
        else:
            error_meta = {
                "method": "client_transaction.views.success_survey",
                "survey_uuid": survey_uuid,
                "previous_state_id": str(previous_state.id)
            }
            ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
            raise SuspiciousOperation('Error Code: 52')
