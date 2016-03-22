from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import permission_required
from models import TransactionUpdateLog, VideoAuthoriseLog, SurveyAuthoriseLog
from ipware.ip import get_real_ip
from promoter_transaction.models import PromoterTransactionLog
from video.models import Video, VideoState
from video.views import watch
from survey.models import Survey, SurveyState


# TODO: iske views kab banaega chuu
@permission_required('staff_custom.access_staff', login_url='/')
def home(request):
    return render(request, 'staff/staff_home.html')


@permission_required('staff_custom.access_staff', login_url='/')
def paytm_recharge_home(request):
    paytm_transactions = PromoterTransactionLog.objects.get_paytm_transactions()
    context = {
        "paytm_transactions": paytm_transactions
    }
    return render(request, 'staff/paytm_transaction_home.html', context)


@permission_required('staff_custom.access_staff', login_url='/')
def paytm_recharge_paid(request, transaction_uuid):
    if request.POST:
        paytm_transaction_id = request.POST.get('paytm_transaction_id')

        try:
            transaction = PromoterTransactionLog.objects.get_transaction(transaction_uuid)
        except:
            return JsonResponse({"updated": False})

        if not transaction.paid:
            staff = request.user.staffprofile

            extra_old_value = transaction.extra.get('paytm_transaction_id', "")
            extra_new_value = paytm_transaction_id

            transaction.paid = True
            extra = transaction.extra

            # TODO: What to save in extra hstore of transaction??
            extra['paytm_transaction_id'] = paytm_transaction_id

            transaction.extra = extra
            transaction.save()
            # todo: on signal all update
            fields_updated = {
                "extra_transaction_id_old": str(extra_old_value), "extra_transaction_id_new": str(extra_new_value),
                "paid_old": "False",
                "paid_new": "True",
            }
            TransactionUpdateLog.objects.create_transaction_update(transaction, staff, fields_updated)

        return JsonResponse({"updated": True})
    else:
        return JsonResponse({"updated": False})


@permission_required('staff_custom.access_staff', login_url='/')
def video_authentication_home(request):
    videos = Video.objects.get_videos_for_authentication()
    context = {
        "videos": videos
    }
    return render(request, 'staff/video_authentication_home.html', context)


@permission_required('staff_custom.access_staff', login_url='/')
def staff_video_watch(request, video_uuid):
    try:
        video = Video.objects.get_video(video_uuid)
    except:
        return HttpResponse('Video not Found')
    else:
        previous_state = video.get_previous_state()
        if previous_state.current in ['ED', 'TC']:
            # return watch(request, video)
            context = {
                "video": video
            }
            return render(request, "staff/staff_playback.html", context)
        else:
            return HttpResponse("Video State Error")


@permission_required('staff_custom.access_staff', login_url='/')
def authorise_activate_video(request, video_uuid):
    try:
        video = Video.objects.get_video(video_uuid)
        staff = request.user.staffprofile
    except:
        return HttpResponse("Video Not Found")
    else:
        try:
            previous_state = video.get_previous_state()
        except VideoState.DoesNotExist:
            return HttpResponse("Video State Error")
        else:
            if previous_state.current in ['TC', 'ED', 'ES']:
                video.create_state(previous_state, 'AA')

                fields_updated = {
                    "status_old": previous_state.current,
                    "status_new": 'AA'
                }
                video.active = True
                video.save()

                VideoAuthoriseLog.objects.create(video_id=video, staff_id=staff, fields_updated=fields_updated)
                return redirect('/staff/video_authentication_home/')
            else:
                return HttpResponse("Video Status Error")


def survey_authentication_home(request):
    surveys = Survey.objects.get_surveys_for_authentication()
    context = {
        "surveys": surveys
    }
    return render(request, 'staff/survey_authentication_home.html', context)


def display_survey(request, survey_uuid):
    try:
        survey = Survey.objects.get_survey(survey_uuid)
    except:
        return HttpResponse("Survey Not Found")
    else:
        previous_state = survey.get_previous_state()
        if previous_state.current in ['ED', 'TC']:
            question_set = survey.questionset_set.all()
            context = {
                "survey": survey,
                "question_set": question_set
            }
            return render(request, 'staff/display_survey.html', context)
        else:
            return HttpResponse('Survey State Error')


def authorise_activate_survey(request, survey_uuid):
    try:
        survey = Survey.objects.get_survey(survey_uuid)
        staff = request.user.staffprofile
    except:
        return HttpResponse("Not Found")
    else:
        try:
            previous_state = survey.get_previous_state()
        except SurveyState.DoesNotExist:
            return HttpResponse('Survey State Error')
        else:
            if previous_state in ['TC', 'ED']:
                survey.create_state(previous_state, 'AA')
                fields_updated = {
                    "status_old": previous_state.current,
                    "status_new": 'AA'
                }
                survey.active = True
                survey.save()
                SurveyAuthoriseLog.objects.create(survey_id=survey, staff_id=staff, fields_updated=fields_updated)
                return redirect('/staff/survey_authentication_home/')
            else:
                return HttpResponse("Video Status error")


@permission_required('staff_custom.access_staff', login_url='/')
def reject_survey(request, survey_uuid):
    if request.POST:
        try:
            survey = Survey.objects.get_survey(survey_uuid)
            staff = request.user.staffprofile
        except:
            return HttpResponse('Not Found')
        else:
            try:
                previous_state = survey.get_previous_state()
            except SurveyState.DoesNotExist:
                return HttpResponse('Survey State Error 1')
            else:
                if previous_state.current in ['TC', 'ED']:
                    question_error = request.POST.get('question_error')
                    info_error = request.POST.get('info_error')
                    error_meta = {
                        "message": request.POST['error_message']
                    }
                    if question_error:
                        error_meta.update({"question_error": "True"})
                    if info_error:
                        error_meta.update({"info_error": "True"})
                    survey.create_state(previous_state, 'EA', error_meta)

                    fields_updated = {
                        "status_old": previous_state.current,
                        "status_new": 'EA'
                    }
                    SurveyAuthoriseLog.objects.create(survey_id=survey, staff_id=staff, fields_updated=fields_updated)
                    return redirect('/staff/survey_authentication_home/')
                else:
                    return HttpResponse('Survey State Error 2')
    else:
        return HttpResponse('No Post')


def delete_staff_user(request):
    # TODO: Add additional related tasks
    request.user.set_user_inactive()
    logout(request)
    return HttpResponse("Account deactivated")


@permission_required('staff_custom.access_staff', login_url='/')
def reject_video(request, video_uuid):
    if request.POST:
        try:
            video = Video.objects.get_video(video_uuid)
            staff = request.user.staffprofile
        except:
            return HttpResponse("Video Not Found")
        else:
            try:
                previous_state = video.get_previous_state()
            except VideoState.DoesNotExist:
                return HttpResponse("Video State Error")
            else:
                if previous_state.current in ['TC', 'ED']:
                    file_error = request.POST.get('file_error')
                    info_error = request.POST.get('info_error')
                    error_meta = {
                        "message": request.POST['error_message']
                    }
                    if file_error:
                        error_meta.update({"file_error": "True"})
                    if info_error:
                        error_meta.update({"info_error": "True"})
                    video.create_state(previous_state, 'EA', error_meta)

                    fields_updated = {
                        "status_old": previous_state.current,
                        "status_new": 'EA'
                    }

                    VideoAuthoriseLog.objects.create(video_id=video, staff_id=staff, fields_updated=fields_updated)
                    return redirect('/staff/video_authentication_home/')
                else:
                    return HttpResponse("Video Status Error")
    else:
        return HttpResponse('Error No post')
