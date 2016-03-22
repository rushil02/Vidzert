import datetime
from django.db.models import Count, Sum, F
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from admin_custom.models import ErrorLog, ActivityLog
from forms import ClientProfileForm
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from promoter.models import PromoterProfile
from video.models import Video, VideoProfile, VideoInfo, VideoFile, VideoInsights, VideoState
from video.forms import VideoUploadForm, VideoInfoForm, VideoProfileForm, VideoAccountForm, VideoFileForm, \
    VideoReviseForm
from survey.models import Survey, SurveyInfo, SurveyProfile, QuestionSet, Question, SurveyState
from survey.forms import QuestionSetFormSet, QuestionFormSet, SurveyForm, SurveyInfoForm, SurveyAccountForm, \
    SurveyProfileForm
from video.tasks import create_thumbnail_async, secure_conv_video, set_duration
from graph.tasks import video_graph_async


@permission_required('client.access_client')
def home(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.home",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    all_video = client_profile.video_set.select_related('videoinsights')
    all_survey = client_profile.survey_set.all().select_related('surveyinsights')

    video_totals = client_profile.video_set.all().aggregate(
        viewers=Sum(F('videoinsights__promoters') + F('videoinsights__anonymous_viewers')),
        engagement=Sum('videoinsights__redirection_click'), expenditure=Sum('videoaccount__video_cost'))
    survey_totals = client_profile.survey_set.all().aggregate(fills=Sum('surveyinsights__promoters'),
                                                              expenditure=Sum('surveyaccount__survey_cost'))

    context = {
        "all_videos": all_video,
        "all_surveys": all_survey,
        "video_totals": video_totals,
        "survey_totals": survey_totals,
    }
    activity_meta = {
        "method": "client.views.home",
    }
    ActivityLog.objects.create_log(request, "Client HomePage", activity_meta)
    return render(request, 'client/home_page.html', context)


@permission_required('client.access_client')
def insights(request, video_uuid):  # FIXME: return video file too
    try:
        video = Video.objects.select_related('videoinsights', 'videofile').get_from_uuid(video_uuid)
    except (ObjectDoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.insights",
            "video_uuid": video_uuid
        }
        ErrorLog.objects.create_log(3, "Video Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 3')

    video_list = []

    (gender_insight, state_insight, age_insights) = profile_insights(video)
    video_insights = video.videoinsights
    video_list.append({
        "video": video,
        "video_insights": video_insights,
        "gender_insight": gender_insight,
        "state_insight": state_insight,
        # "gender_engagement_insight": gender_engagement_insight,
        # "state_engagement_insight": state_engagement_insight,
        "age_insights": age_insights
    })

    child_videos = video.get_child_videos().select_related('videoinsights')
    for child_video in child_videos:
        (child_gender_insight, child_state_insight, child_age_insights) = profile_insights(child_video)
        child_video_insights = child_video.videoinsights
        video_list.append({
            "video": child_video,
            "video_insights": child_video_insights,
            "gender_insight": child_gender_insight,
            "state_insight": child_state_insight,
            # "gender_engagement_insight": child_gender_engagement_insight,
            # "state_engagement_insight": child_state_engagement_insight,
            "age_insights": child_age_insights
        })

    context = {
        "video": video,
        "video_list": video_list
    }
    activity_meta = {
        "method": "client.views.insights",
        "video_uuid": video_uuid
    }
    ActivityLog.objects.create_log(request, "Get Video Insights", activity_meta)
    return render(request, 'client/video_insight.html', context)


@permission_required('client.access_client')
def all_videos(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.all_videos",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    active_videos = client_profile.video_set.get_active().order_by(
        'update_time').select_related('videoinsights', 'videofile')
    payment_due_videos = client_profile.video_set.get_payment_due_videos()
    file_upload_due_videos = client_profile.video_set.get_file_upload_due_videos()
    in_auth_process_videos = client_profile.video_set.get_in_auth_process_videos()
    edit_videos = client_profile.video_set.get_edit_videos()
    completed_videos = client_profile.video_set.get_completed_videos().select_related('videoinsights', 'videofile')
    error_videos = client_profile.video_set.get_error_videos()

    context = {
        "active_videos": active_videos,
        "payment_due_videos": payment_due_videos,
        "file_upload_due_videos": file_upload_due_videos,
        "in_auth_process_videos": in_auth_process_videos,
        "edit_videos": edit_videos,
        "completed_videos": completed_videos,
        "error_videos": error_videos
    }
    activity_meta = {
        "method": "client.views.home",
    }
    ActivityLog.objects.create_log(request, "Client HomePage", activity_meta)
    return render(request, 'client/all_videos.html', context)


@permission_required('client.access_client')
def all_surveys(request):  # FIXME: create simliar to all_video
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.all_surveys",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    active_surveys = client_profile.survey_set.filter(active=True).order_by('-update_time')
    inactive_surveys = client_profile.survey_set.filter(active=False).order_by('-update_time')

    context = {
        "active_surveys": active_surveys,
        "inactive_surveys": inactive_surveys,
    }
    activity_meta = {
        "method": "client.views.home",
    }
    ActivityLog.objects.create_log(request, "Client HomePage", activity_meta)
    return render(request, 'client/all_surveys.html', context)


@permission_required('client.access_client')
def client_profile_view(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.client_profile_view",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')
    context = {
        "profile": client_profile
    }
    activity_meta = {
        "method": "client.views.client_profile_view",
    }
    ActivityLog.objects.create_log(request, "View Client Account", activity_meta)
    return render(request, "client/profile.html", context)


@permission_required('client.access_client')
def update_client_profile(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.update_client_profile",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')
    form = ClientProfileForm(request.POST or None, instance=client_profile, name=request.user.name)
    context = {
        "form": form
    }
    if request.POST:
        if form.is_valid():
            form.save()
            activity_meta = {
                "method": "client.views.update_client_profile",
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, "Update Client Account", activity_meta)
            return redirect('/cl/profile/')
        else:
            return render(request, "client/edit_profile.html", context)
    else:
        activity_meta = {
            "method": "client.views.update_client_profile",
        }
        ActivityLog.objects.create_log(request, "Update Client Account", activity_meta)
        return render(request, "client/edit_profile.html", context)


@permission_required('client.access_client')
def upload(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.upload",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    if request.POST:
        video_form = VideoUploadForm(request.POST)
        video_info_form = VideoInfoForm(request.POST, request.FILES)
        video_profile_form = VideoProfileForm(request.POST)
        video_account_form = VideoAccountForm(request.POST)
        context = {
            "video_form": video_form,
            "video_info_form": video_info_form,
            "video_profile_form": video_profile_form,
            "video_account_form": video_account_form,
        }
        if video_form.is_valid() and video_info_form.is_valid() and video_profile_form.is_valid() and \
                video_account_form.is_valid():

            with transaction.atomic():
                video = video_form.save(commit=False)
                video.client_id = client_profile
                # Do other Stuff before upload like generate graph, url and do form.save()
                video.save()
                video_form.save_m2m()

                VideoInsights.objects.create(video_id=video)

                video_info = video_info_form.save(commit=False)
                video_info.video_id = video
                video_info.save()

                video_profile = video_profile_form.save(commit=False)
                video_profile.video_id = video
                video_profile.save()
                video_profile_form.save_m2m()

                video_account = video_account_form.save(commit=False)
                video_account.video_id = video
                video_account.save()

                previous_state = None
                video.create_state(previous_state, 'IF')

            activity_meta = {
                "method": "client.views.upload",
                "video_uuid": str(video.uuid),
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, "Upload Video", activity_meta)
            return redirect('/cl/payment/success_v/' + str(video.uuid) + '/')  # FIXME: Redirect to payment gateway
        else:
            return render(request, "video/upload.html", context)
    else:
        video_form = VideoUploadForm()
        video_info_form = VideoInfoForm()
        video_profile_form = VideoProfileForm()
        video_account_form = VideoAccountForm()
        context = {
            "video_form": video_form,
            "video_info_form": video_info_form,
            "video_profile_form": video_profile_form,
            "video_account_form": video_account_form,
        }
        activity_meta = {
            "method": "client.views.upload",
        }
        ActivityLog.objects.create_log(request, "Upload Video", activity_meta)
        return render(request, "video/upload.html", context)


@permission_required('client.access_client')
def upload_video_file(request, video_uuid):  # TODO: error log, activity log and other shit
    try:
        video = Video.objects.get_video(video_uuid)
    except (Video.DoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.upload_video_file",
            "video_uuid": video_uuid
        }
        ErrorLog.objects.create_log(3, "Video Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 3')

    try:
        previous_state = video.get_previous_state()
    except VideoState.DoesNotExist:
        error_meta = {
            "method": "client.views.upload_video_file",
            "video_uuid": video_uuid,
        }
        ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 51')

    if previous_state.current == 'PA':
        if request.POST:
            video_file_form = VideoFileForm(request.POST, request.FILES)
            context = {
                "video_file_form": video_file_form
            }
            if video_file_form.is_valid():
                video_file = video_file_form.save(commit=False)
                video_file.video_id = video
                video_file.save()

                video.create_state(previous_state, 'VU')

                client_user = request.user

                if video_file.thumbnail_image:
                    (secure_conv_video.si(
                        video.id, client_user.id, True,
                    ) | set_duration.si(
                        video.id, client_user.id, True
                    ) | video_graph_async.si(
                        video.id, client_user.id, True
                    )).apply_async(countdown=2)
                else:
                    (secure_conv_video.si(
                        video.id, client_user.id, True,
                    ) | create_thumbnail_async.si(
                        video.id, client_user.id, True
                    ) | set_duration.si(
                        video.id, client_user.id, True
                    ) | video_graph_async.si(
                        video.id, client_user.id, True
                    )).apply_async(countdown=2)

                activity_meta = {
                    "method": "client.views.upload_video_file",
                    "video_uuid": video_uuid,
                    "form_validation": "True"
                }
                ActivityLog.objects.create_log(request, 'Upload Video File', activity_meta)
                return redirect('/cl/')

            else:
                return render(request, 'client/upload_video_file.html', context)
        else:
            video_file_form = VideoFileForm()
            context = {
                "video_file_form": video_file_form
            }
            activity_meta = {
                "method": "client.views.upload_video_file",
                "video_uuid": video_uuid,
            }
            ActivityLog.objects.create_log(request, 'Upload Video File', activity_meta)
            return render(request, 'client/upload_video_file.html', context)
    else:
        error_meta = {
            "method": "client.views.upload_video_file",
            "video_uuid": video_uuid,
            "previous_state_id": str(previous_state.id)
        }
        ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 51')


@permission_required('client.access_client')
def revise(request, video_uuid):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.revise",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    try:
        video = Video.objects.select_related('videoinfo', 'videoprofile', 'videofile').get_from_uuid(video_uuid)
    except (ObjectDoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.revise",
            "video_uuid": video_uuid
        }
        ErrorLog.objects.create_log(3, "Video Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 3')

    new_video = Video(client_id=client_profile,
                      name=video.name,
                      featured=video.featured,
                      publisher=video.publisher,
                      parent_video=video
                      )

    new_video_info = VideoInfo(desc=video.videoinfo.desc,
                               banner_landing_page=video.videoinfo.banner_landing_page,
                               banner_landing_page_image=video.videoinfo.banner_landing_page_image,
                               product_desc=video.videoinfo.product_desc,
                               buy_product=video.videoinfo.buy_product,
                               )
    video_form = VideoReviseForm(request.POST or None, instance=new_video)
    video_info_form = VideoInfoForm(request.POST or None, instance=new_video_info)
    video_account_form = VideoAccountForm(request.POST or None)

    context = {
        "video_form": video_form,
        "video_info_form": video_info_form,
        "video_account_form": video_account_form
    }

    if request.POST:
        if video_form.is_valid and video_account_form.is_valid() and video_info_form.is_valid():
            video_account = video_account_form.save(commit=False)

            categories = video.category.all()
            video_form.save()
            new_video.category = categories

            new_video_info = video_info_form.save(commit=False)
            new_video_info.video_id = new_video
            new_video_info.save()

            states = video.videoprofile.state.all()
            new_video_profile = VideoProfile(video_id=new_video,
                                             age=video.videoprofile.age,
                                             gender=video.videoprofile.gender,
                                             city=video.videoprofile.city,
                                             )
            new_video_profile.save()
            new_video_profile.state = states

            video_account.video_id = new_video
            video_account.save()

            VideoInsights.objects.create(video_id=video)

            new_video_file = VideoFile(video_id=new_video,
                                       video_file_orig=video.videofile.video_file_orig,
                                       thumbnail_image=video.videofile.thumbnail_image,
                                       video_file_mp4=video.videofile.video_file_mp4,
                                       video_file_webm=video.videofile.video_file_webm,
                                       video_duration=video.videofile.video_duration)
            new_video_file.save()

            previous_state = None
            video.create_state(previous_state, 'IF')

            activity_meta = {
                "method": "client.views.revise",
                "video_uuid": video_uuid,
                "video_cost": request.POST.get('video_cost')
            }
            ActivityLog.objects.create_log(request, "Revise Video", activity_meta)
            return HttpResponse("Success")  # FIXME
        else:
            return render(request, 'client/revise.html', context)
    else:
        activity_meta = {
            "method": "client.views.revise",
            "video_uuid": video_uuid
        }
        ActivityLog.objects.create_log(request, "Revise Video", activity_meta)
        return render(request, "client/revise.html", context)


@permission_required('client.access_client')
def create_survey(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.revise",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    if request.POST:
        survey_form = SurveyForm(request.POST)
        survey_info_form = SurveyInfoForm(request.POST, request.FILES)
        survey_profile_form = SurveyProfileForm(request.POST)
        survey_account_form = SurveyAccountForm(request.POST)
        context = {
            "survey_form": survey_form,
            "survey_info_form": survey_info_form,
            "survey_profile_form": survey_profile_form,
            "survey_account_form": survey_account_form,
        }
        if survey_form.is_valid() and survey_info_form.is_valid() and survey_profile_form.is_valid() and \
                survey_account_form.is_valid():
            survey = survey_form.save(commit=False)
            survey.client_id = client_profile
            survey.save()
            survey_form.save_m2m()

            survey_info = survey_info_form.save(commit=False)
            survey_info.survey_id = survey
            survey_info.save()

            survey_profile = survey_profile_form.save(commit=False)
            survey_profile.survey_id = survey
            survey_profile.save()
            survey_profile_form.save_m2m()

            survey_account = survey_account_form.save(commit=False)
            survey_account.survey_id = survey
            survey_account.save()

            previous_state = None
            survey.create_state(previous_state, 'IF')

            activity_meta = {
                "method": "client.views.create_survey",
                "survey_uuid": str(survey.uuid),
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, "Create Survey", activity_meta)
            return redirect('/cl/payment/success_s/' + str(survey.uuid) + '/')  # FIXME: Redirect to payment gateway
        else:
            return render(request, "survey/create_survey.html", context)
    else:
        survey_form = SurveyForm()
        survey_info_form = SurveyInfoForm()
        survey_profile_form = SurveyProfileForm()
        survey_account_form = SurveyAccountForm()
        context = {
            "survey_form": survey_form,
            "survey_info_form": survey_info_form,
            "survey_profile_form": survey_profile_form,
            "survey_account_form": survey_account_form,
        }
        activity_meta = {
            "method": "client.views.create_survey",
        }
        ActivityLog.objects.create_log(request, "Create Survey", activity_meta)
        return render(request, "survey/create_survey.html", context)


@permission_required('client.access_client')
def create_question_set(request, survey_uuid):
    try:
        survey = Survey.objects.get_survey(survey_uuid)
    except (Survey.DoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.create_question_set",
            "survey_uuid": survey_uuid
        }
        ErrorLog.objects.create_log(7, "Survey Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 7')

    try:
        previous_state = survey.get_previous_state()
    except SurveyState.DoesNotExist:
        error_meta = {
            "method": "client.views.create_question_set",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')

    if previous_state.current in ['PA', 'EA']:
        question_set = survey.questionset_set.all()
        question_set_formset = QuestionSetFormSet(request.POST or None, instance=survey)

        context = {
            "survey": survey,
            "question_sets": question_set,
            "question_set_formset": question_set_formset,
        }
        if previous_state.current == 'EA':
            error_message = previous_state.error_meta.get('message')
            context.update({"error_message": error_message})
        if request.POST:
            if question_set_formset.is_valid():
                question_set_formset.save()
                activity_meta = {
                    "method": "client.views.create_question_set",
                    "survey_uuid": survey_uuid,
                    "form_validation": "True"
                }
                ActivityLog.objects.create_log(request, 'Create Question Set', activity_meta)
                return redirect('/cl/create_survey/' + survey_uuid + '/')
            else:
                return render(request, 'survey/view_question_set.html', context)
        else:
            activity_meta = {
                "method": "client.views.create_question_set",
                "survey_uuid": survey_uuid,
            }
            ActivityLog.objects.create_log(request, 'Create Question Set', activity_meta)
            return render(request, 'survey/view_question_set.html', context)
    else:
        error_meta = {
            "method": "client.views.create_question_set",
            "survey_uuid": survey_uuid,
            "previous_state_id": str(previous_state.id)
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')


@permission_required('client.access_client')
def create_question(request, survey_uuid, question_set_id):
    try:
        survey = Survey.objects.get_survey(survey_uuid)
        questionset = survey.questionset_set.get(id=question_set_id)
        questions = questionset.question_set.all()
    except (ObjectDoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.create_question",
            "survey_uuid": survey_uuid,
            "question_set_id": question_set_id
        }
        ErrorLog.objects.create_log(7, "Survey Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 7')

    try:
        previous_state = survey.get_previous_state()
    except SurveyState.DoesNotExist:
        error_meta = {
            "method": "client.views.create_question",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')

    if previous_state.current in ['PA', 'EA']:
        question_formset = QuestionFormSet(request.POST or None, instance=questionset)
        context = {
            "survey": survey,
            "question_set": questionset,
            "questions": questions,
            "question_formset": question_formset,
        }
        if request.POST:
            if question_formset.is_valid():
                question_formset.save()
                activity_meta = {
                    "method": "client.views.create_question",
                    "survey_uuid": survey_uuid,
                    "question_set_id": question_set_id,
                    "form_validation": "True"
                }
                ActivityLog.objects.create_log(request, 'Create Question', activity_meta)
                return redirect("/cl/create_survey/" + str(survey.uuid) + "/" + str(questionset.id))
            else:
                return render(request, 'survey/view_questions.html', context)
        else:
            activity_meta = {
                "method": "client.views.create_question",
                "survey_uuid": survey_uuid,
                "question_set_id": question_set_id,
            }
            ActivityLog.objects.create_log(request, 'Create Question', activity_meta)
            return render(request, 'survey/view_questions.html', context)
    else:
        error_meta = {
            "method": "client.views.create_question",
            "survey_uuid": survey_uuid,
            "previous_state_id": str(previous_state.id)
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')


def survey_activate_request(request, survey_uuid):
    try:
        survey = Survey.objects.get_survey(survey_uuid)
    except (Survey.DoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.survey_activate_request",
            "survey_uuid": survey_uuid
        }
        ErrorLog.objects.create_log(7, "Survey Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 7')

    try:
        previous_state = survey.get_previous_state()
    except SurveyState.DoesNotExist:
        error_meta = {
            "method": "client.views.survey_activate_request",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')

    if previous_state.current in ['PA', 'EA']:
        # TODO: Check if question or question set count 0
        if previous_state.current == 'EA':
            survey.create_state(previous_state, 'ED')
        else:
            survey.create_state(previous_state, 'SF')
        return redirect('/cl/surveys/')
    else:
        error_meta = {
            "method": "client.views.survey_activate_request",
            "survey_uuid": survey_uuid,
            "previous_state_id": str(previous_state.id)
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')


@permission_required('client.access_client')
def client_survey_home(request):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.client_survey_home",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    surveys = client_profile.survey_set.all()
    context = {
        "surveys": surveys
    }
    activity_meta = {
        "method": "client.views.client_survey_home"
    }
    ActivityLog.objects.create_log(request, 'Client Survey Home', activity_meta)
    return render(request, "client/survey_home.html", context)


def profile_insights(video):
    # TODO: Can exclude null gender values or state values on front end
    gender_insight = PromoterProfile.objects.filter(videopromoterlog__video_id=video).values('gender') \
        .annotate(count=Count('gender'))
    state_insight = PromoterProfile.objects.filter(videopromoterlog__video_id=video).values('area_state') \
        .annotate(count=Count('area_state'))

    # Age Insights
    age_18 = datetime.datetime.now().date() - datetime.timedelta(days=18 * 365)
    age_25 = datetime.datetime.now().date() - datetime.timedelta(days=25 * 365)
    age_40 = datetime.datetime.now().date() - datetime.timedelta(days=40 * 365)
    age_60 = datetime.datetime.now().date() - datetime.timedelta(days=60 * 365)

    below_18 = PromoterProfile.objects.filter(videopromoterlog__video_id=video, dob__gt=age_18) \
        .exclude(dob__isnull=True).count()
    btw_18_25 = PromoterProfile.objects.filter(videopromoterlog__video_id=video, dob__lte=age_18, dob__gt=age_25) \
        .exclude(dob__isnull=True).count()
    btw_25_40 = PromoterProfile.objects.filter(videopromoterlog__video_id=video, dob__lte=age_25, dob__gt=age_40) \
        .exclude(dob__isnull=True).count()
    btw_40_60 = PromoterProfile.objects.filter(videopromoterlog__video_id=video, dob__lte=age_40, dob__gt=age_60) \
        .exclude(dob__isnull=True).count()
    above_60 = PromoterProfile.objects.filter(videopromoterlog__video_id=video, dob__lte=age_60) \
        .exclude(dob__isnull=True).count()

    age_insights = {
        "below_18": below_18,
        "btw_18_25": btw_18_25,
        "btw_25_40": btw_25_40,
        "btw_40_60": btw_40_60,
        "above_60": above_60,
    }
    return gender_insight, state_insight, age_insights


@permission_required('client.access_client')
def delete_client(request):
    # TODO: Add additional related tasks
    request.user.set_user_inactive()
    logout(request)
    return HttpResponse("Account deactivated")


def revise_survey(request, survey_uuid):
    try:
        client_profile = request.user.clientprofile
    except ObjectDoesNotExist:
        error_meta = {
            "method": "client.views.revise_survey",
        }
        ErrorLog.objects.create_log(8, "Client Object Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 8')

    try:
        survey = Survey.objects.select_related('surveyinfo', 'surveyprofile').get_from_uuid(survey_uuid)
    except (ObjectDoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.create_question",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(7, "Survey Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 7')

    new_survey_info = SurveyInfo(desc=survey.surveyinfo.desc,
                                 banner_landing_page=survey.surveyinfo.banner_landing_page,
                                 banner_landing_page_image=survey.surveyinfo.banner_landing_page_image)

    survey_info_form = SurveyInfoForm(request.POST or None, instance=new_survey_info)
    survey_account_form = SurveyAccountForm(request.POST or None)

    context = {
        "survey_info_form": survey_info_form,
        "survey_account_form": survey_account_form
    }

    if request.POST:
        if survey_info_form.is_valid() and survey_account_form.is_valid():
            new_survey = Survey(client_id=client_profile,
                                title=survey.title,
                                parent_survey=survey
                                )
            new_survey.save()
            categories = survey.category.all()
            new_survey.category = categories

            new_survey_info = survey_info_form.save(commit=False)
            new_survey_info.survey_id = new_survey
            new_survey_info.save()

            survey_account = survey_account_form.save(commit=False)
            survey_account.survey_id = new_survey
            survey_account.save()

            states = survey.surveyprofile.state.all()
            new_survey_profile = SurveyProfile(survey_id=new_survey,
                                               age=survey.surveyprofile.age,
                                               gender=survey.surveyprofile.gender,
                                               city=survey.surveyprofile.city)
            new_survey_profile.save()
            new_survey_profile.state = states

            question_sets = survey.questionset_set.all()

            for questionset in question_sets:
                questions = questionset.question_set.all()
                question_list = []
                new_questionset = QuestionSet.objects.create(survey_id=new_survey, sort_id=questionset.sort_id,
                                                             heading=questionset.heading,
                                                             help_text=questionset.help_text)
                for question in questions:
                    question_list.append(
                        Question(question_set_id=new_questionset, number=question.number, sort_id=question.sort_id,
                                 text=question.text, question_type=question.question_type,
                                 extra_text=question.extra_text, required=question.required,
                                 footer_text=question.footer_text, choices=question.choices))

                Question.objects.bulk_create(question_list)

            previous_state = None
            survey.create_state(previous_state, 'IF')

            activity_meta = {
                "method": "client.views.revise_survey",
                "survey_uuid": survey_uuid,
                "survey_cost": request.POST.get('survey_cost')
            }
            ActivityLog.objects.create_log(request, 'Revise Survey', activity_meta)
            return HttpResponse('Success')  # FIXME
        else:
            return render(request, 'client/revise_survey.html', context)
    else:
        activity_meta = {
            "method": "client.views.revise_survey",
            "survey_uuid": survey_uuid
        }
        ActivityLog.objects.create_log(request, "Revise Survey", activity_meta)
        return render(request, "client/revise_survey.html", context)


def edit_video(request, video, previous_state):
    error_message = previous_state.error_meta.get('message')

    if request.POST:
        video_form = VideoUploadForm(request.POST, instance=video)
        video_info_form = VideoInfoForm(request.POST, request.FILES, instance=video.videoinfo)
        video_profile_form = VideoProfileForm(request.POST, instance=video.videoprofile)
        context = {
            "video_form": video_form,
            "video_info_form": video_info_form,
            "video_profile_form": video_profile_form,
            "error_message": error_message
        }
        if video_form.is_valid() and video_info_form.is_valid() and video_profile_form.is_valid():

            with transaction.atomic():
                video = video_form.save(commit=False)
                video.save()
                video_form.save_m2m()

                video_info_form.save()

                video_profile = video_profile_form.save(commit=False)
                video_profile.save()
                video_profile_form.save_m2m()

                video.create_state(previous_state, 'ED')

            activity_meta = {
                "method": "client.views.edit_video",
                "video_uuid": str(video.uuid),
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, "Edit Video", activity_meta)
            return redirect('/cl/')
        else:
            return render(request, "client/edit_video.html", context)
    else:
        video_form = VideoUploadForm(instance=video)
        video_info_form = VideoInfoForm(instance=video.videoinfo)
        video_profile_form = VideoProfileForm(instance=video.videoprofile)
        context = {
            "video_form": video_form,
            "video_info_form": video_info_form,
            "video_profile_form": video_profile_form,
            "error_message": error_message
        }
        activity_meta = {
            "method": "client.views.edit_video",
            "video_uuid": str(video.uuid)
        }
        ActivityLog.objects.create_log(request, "Edit Video", activity_meta)
        return render(request, "client/edit_video.html", context)


def upload_edit_video(request, video, previous_state):
    error_message = previous_state.error_meta.get('message')

    if request.POST:
        video_form = VideoUploadForm(request.POST, instance=video)
        video_info_form = VideoInfoForm(request.POST, request.FILES, instance=video.videoinfo)
        video_profile_form = VideoProfileForm(request.POST, instance=video.videoprofile)
        video_file_form = VideoFileForm(request.POST, request.FILES)
        context = {
            "video_form": video_form,
            "video_info_form": video_info_form,
            "video_profile_form": video_profile_form,
            "video_file_form": video_file_form,
            "error_message": error_message
        }
        if video_form.is_valid() and video_info_form.is_valid() and video_profile_form.is_valid() and \
                video_file_form.is_valid():

            with transaction.atomic():
                video.videofile.delete()

                video = video_form.save(commit=False)
                video.save()
                video_form.save_m2m()

                video_info_form.save()

                video_profile = video_profile_form.save(commit=False)
                video_profile.save()
                video_profile_form.save_m2m()

                video_file = video_file_form.save(commit=False)
                video_file.video_id = video
                video_file.save()

                video.create_state(previous_state, 'VU')

            client_user = request.user

            if video_file.thumbnail_image:
                (secure_conv_video.si(
                    video.id, client_user.id, True
                ) | set_duration.si(
                    video.id, client_user.id, True, 'VU', 'TC'
                )).apply_async(countdown=2)
            else:
                (secure_conv_video.si(
                    video.id, client_user.id, True,
                ) | create_thumbnail_async.si(
                    video.id, client_user.id, True
                ) | set_duration.si(
                    video.id, client_user.id, True, 'VU', 'TC'
                )).apply_async(countdown=2)

            activity_meta = {
                "method": "client.views.file_error",
                "video_uuid": str(video.uuid),
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, "Edit Video", activity_meta)
            return redirect('/cl/')
        else:
            return render(request, "client/edit_video.html", context)
    else:
        video_form = VideoUploadForm(instance=video)
        video_info_form = VideoInfoForm(instance=video.videoinfo)
        video_profile_form = VideoProfileForm(instance=video.videoprofile)
        video_file_form = VideoFileForm()
        context = {
            "video_form": video_form,
            "video_info_form": video_info_form,
            "video_profile_form": video_profile_form,
            "video_file_form": video_file_form,
            "error_message": error_message
        }
        activity_meta = {
            "method": "client.views.file_error",
            "video_uuid": str(video.uuid)
        }
        ActivityLog.objects.create_log(request, "Edit Video", activity_meta)
        return render(request, "client/edit_video.html", context)


def edit_video_file(request, video, previous_state):
    error_message = previous_state.error_meta.get('message')

    if request.POST:
        video_file_form = VideoFileForm(request.POST, request.FILES)
        context = {
            "error_message": error_message,
            "video_file_form": video_file_form
        }
        if video_file_form.is_valid():
            video.videofile.delete()
            video_file = video_file_form.save(commit=False)
            video_file.video_id = video
            video_file.save()

            video.create_state(previous_state, 'VU')

            activity_meta = {
                "method": "client.views.edit_video_file",
                "video_uuid": str(video.uuid),
                "form_validation": "True"
            }
            ActivityLog.objects.create_log(request, 'Edit Video', activity_meta)
            return redirect('/cl/')
        else:
            return render(request, 'client/upload_video_file.html', context)
    else:
        video_file_form = VideoFileForm()
        context = {
            "video_file_form": video_file_form,
            "error_message": error_message
        }
        activity_meta = {
            "method": "client.views.edit_video_file",
            "video_uuid": str(video.uuid),
        }
        ActivityLog.objects.create_log(request, 'Edit Video', activity_meta)
        return render(request, 'client/upload_video_file.html', context)


@permission_required('client.access_client')
def edit_handler(request, video_uuid):
    try:
        video = Video.objects.select_related('videoinfo', 'videoprofile', 'videofile').get_from_uuid(video_uuid)
    except (ObjectDoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.edit_handler",
            "video_uuid": video_uuid
        }
        ErrorLog.objects.create_log(3, "Video Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 3')

    try:
        previous_state = video.get_previous_state()
    except VideoState.DoesNotExist:
        error_meta = {
            "method": "client.views.edit_handler",
            "video_uuid": video_uuid,
        }
        ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 51')

    if previous_state.current == 'EA':
        if previous_state.error_meta.get('info_error') and previous_state.error_meta.get('file_error'):
            return upload_edit_video(request, video, previous_state)
        elif previous_state.error_meta.get('info_error'):
            return edit_video(request, video, previous_state)
        elif previous_state.error_meta.get('file_error'):
            return edit_video_file(request, video, previous_state)
        else:
            error_meta = {
                "method": "client.views.edit_handler",
                "video_uuid": video_uuid,
                "previous_state_id": str(previous_state.id)
            }
            ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
            raise SuspiciousOperation('Error Code: 51')
    elif previous_state.current == 'EC':
        return edit_video_file(request, video, previous_state)
    else:
        error_meta = {
            "method": "client.views.edit_handler",
            "video_uuid": video_uuid,
            "previous_state_id": str(previous_state.id)
        }
        ErrorLog.objects.create_log(51, "Client Video Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 51')


@permission_required('client.access_client')
def edit_survey_handler(request, survey_uuid):
    try:
        survey = Survey.objects.select_related('surveyinfo', 'surveyprofile').get_from_uuid(survey_uuid)
    except (ObjectDoesNotExist, ValueError):
        error_meta = {
            "method": "client.views.edit_survey_handler",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(7, "Survey Object Error", error_meta, request)
        return SuspiciousOperation('Error Code: 7')

    try:
        previous_state = survey.get_previous_state()
    except SurveyState.DoesNotExist:
        error_meta = {
            "method": "client_transaction.views.edit_survey_handler",
            "survey_uuid": survey_uuid,
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')

    if previous_state.current == 'EA':
        if previous_state.error_meta.get('info_error') and previous_state.error_meta.get('question_error'):
            return edit_survey_info(request, survey, previous_state, question_error=True)
        elif previous_state.error_meta.get('info_error'):
            return edit_survey_info(request, survey, previous_state)
        elif previous_state.error_meta.get('question_error'):
            return redirect('/cl/create_survey/' + str(survey.uuid) + '/')
        else:
            error_meta = {
                "method": "client_transaction.views.edit_survey_handler",
                "survey_uuid": survey_uuid,
                "previous_state_id": str(previous_state.id)
            }
            ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
            raise SuspiciousOperation('Error Code: 52')
    else:
        error_meta = {
            "method": "client_transaction.views.edit_survey_handler",
            "survey_uuid": survey_uuid,
            "previous_state_id": str(previous_state.id)
        }
        ErrorLog.objects.create_log(52, "Client Survey Status Error", error_meta, request)
        raise SuspiciousOperation('Error Code: 52')


def edit_survey_info(request, survey, previous_state, question_error=False):
    error_message = previous_state.error_meta.get('message')

    if request.POST:
        survey_form = SurveyForm(request.POST, instance=survey)
        survey_info_form = SurveyInfoForm(request.POST, request.FILES, instance=survey.surveyinfo)
        survey_profile_form = SurveyProfileForm(request.POST, instance=survey.surveyprofile)

        context = {
            "survey_form": survey_form,
            "survey_info_form": survey_info_form,
            "survey_profile_form": survey_profile_form,
            "error_message": error_message
        }
        if survey_form.is_valid() and survey_info_form.is_valid() and survey_profile_form.is_valid():
            with transaction.atomic():
                survey = survey_form.save(commit=False)
                survey.save()
                survey_form.save_m2m()

                survey_info_form.save()

                survey_profile = survey_profile_form.save(commit=False)
                survey_profile.save()
                survey_profile_form.save_m2m()

                activity_meta = {
                    "method": "client.views.edit_survey_info",
                    "survey_uuid": str(survey.uuid),
                    "form_validation": "True"
                }
                ActivityLog.objects.create_log(request, "Edit Survey", activity_meta)

                if question_error:
                    return redirect('/cl/create_survey/' + str(survey.uuid) + '/')
                else:
                    survey.create_state(previous_state, 'ED')
                    return redirect('/cl/')
        else:
            return render(request, 'client/edit_survey.html', context)
    else:
        survey_form = SurveyForm(instance=survey)
        survey_info_form = SurveyInfoForm(instance=survey.surveyinfo)
        survey_profile_form = SurveyProfileForm(instance=survey.surveyprofile)
        context = {
            "survey_form": survey_form,
            "survey_info_form": survey_info_form,
            "survey_profile_form": survey_profile_form,
            "error_message": error_message
        }
        activity_meta = {
            "method": "client.views.edit_survey_info",
            "survey_uuid": str(survey.uuid),
            "form_validation": "True"
        }
        ActivityLog.objects.create_log(request, "Edit Survey", activity_meta)
        return render(request, 'client/edit_survey.html', context)
