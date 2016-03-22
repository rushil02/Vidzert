from __future__ import absolute_import

import os
import time

from django.db import transaction

from django.conf import settings

from Vidzert.celery import app
from admin_custom.custom_errors import GraphError, VideoStateError, ForceTerminate
from .graph_generator import VideoGraph, SurveyGraph
from .models import Graph
from admin_custom.models import ErrorLog
from survey.models import Survey
from video.models import Video, VideoState
from django.contrib.auth import get_user_model


@app.task(name='generate_graph.video', throws=(GraphError, VideoStateError, ForceTerminate))
def video_graph_async(video_id, client_user_id, video_state_aware=True, curr_state='VC', nxt_state='TC'):
    video = Video.objects.get(id=video_id)

    user = get_user_model().objects.get(id=client_user_id)
    if video_state_aware:
        previous_state = video.get_previous_state()
        if previous_state.current != curr_state:
            if previous_state.current == 'FT':
                raise ForceTerminate
            else:
                error_meta = ({"video_id": str(video.id), "ERROR": "VideoStateError",
                               "VideoState": previous_state.current})
                ErrorLog.objects.create(error_code=300, error_type="Graph_Error", error_meta=error_meta, actor=user)
                raise VideoStateError

    save_time = video.create_time
    path1 = time.strftime('/%Y/%m/%d/', save_time.timetuple())

    # Check and create for directories
    complete_file_path = os.path.join(settings.MEDIA_ROOT, ('Graph/Video' + path1))
    if not os.path.exists(complete_file_path):
        os.makedirs(complete_file_path)

    file_name = str(video.uuid)

    video_account = video.videoaccount

    cost = video_account.video_cost
    featured = video.featured

    file_location = 'Graph/Video' + path1 + (file_name + '.png')

    complete_file_location = os.path.join(settings.MEDIA_ROOT, ('Graph/Video' + path1),
                                          (file_name + '.png'))
    i_for_rename = 1
    while os.path.exists(complete_file_location):
        file_location = 'Graph/Video' + path1 + (file_name + '(' + i_for_rename + ')' + '.png')
        complete_file_location = os.path.join(settings.MEDIA_ROOT, ('Graph/Video' + path1),
                                              (file_name + '(' + i_for_rename + ')' + '.png'))
        i_for_rename += 1

    error_meta = {}

    graph = VideoGraph(money=cost, featured=featured)

    jump_over = False

    try:
        max_coin = graph.generate_model()

    except AssertionError:
        if video_state_aware:
            error_meta, jump_over, marker = test_state_video(video, curr_state)
            if marker:
                raise ForceTerminate

        if not jump_over:
            error_meta = graph.error_meta
            error_meta.update({"ERROR": "Assertion Error in graph generate"})
            raise GraphError('Video graph creation Failed')

    except Exception:
        if video_state_aware:
            error_meta, jump_over, marker = test_state_video(video)
            if marker:
                raise ForceTerminate

        if not jump_over:
            error_meta = graph.error_meta
            error_meta.update({"ERROR": "Unknown Error, probably system memory error, not yet tried to save"})
            raise GraphError('Unknown Error, Please check Error Log')

    else:
        try:
            with transaction.atomic():
                if video_state_aware:
                    previous_state = video.get_previous_state()
                    if previous_state.current == 'FT':
                        raise ForceTerminate
                    elif previous_state.current == curr_state:
                        video.create_state(previous_state, nxt_state)
                    else:
                        raise VideoStateError

                error_meta = graph.error_meta
                video.max_coins = max_coin
                video.save()

                video_account.max_viewership = graph.people
                graph_obj = Graph.objects.create(graph_model=graph.model_dict,
                                                 graph_user=graph.user_dict, user_pos=graph.user_pos_dict,
                                                 stats=graph.stats, graph_file=file_location)
                video_account.graph_id = graph_obj
                video_account.save()

        except VideoStateError:
            error_meta.update({"ERROR": "Invalid Video state", "VideoState": previous_state.current})
            jump_over = True

        except Exception:
            if video_state_aware:
                error_meta, jump_over, marker = test_state_video(video, curr_state)
                if marker:
                    raise ForceTerminate

            if not jump_over:
                error_meta = graph.error_meta
                error_meta.update(
                    {"ERROR": "Unknown Error in transaction.atomic block, probably django SQL memory error"}
                )
                raise GraphError('Unknown Error, Please check Error Log')

        else:
            graph.plot_graph(complete_file_location, file_name)

    finally:
        if bool(error_meta):
            error_meta.update({"video_id": str(video.id)})
            if jump_over:
                ErrorLog.objects.create(error_code=310, error_type="VideoStateError", error_meta=error_meta, actor=user)
                raise VideoStateError
            else:
                ErrorLog.objects.create(error_code=300, error_type="Graph_Error", error_meta=error_meta, actor=user)


@app.task(name='generate_graph.survey', throws=(GraphError,))
def survey_graph_async(survey_id, client_user_id):
    survey = Survey.objects.get(id=survey_id)
    user = get_user_model().objects.get(id=client_user_id)

    save_time = survey.create_time
    path1 = time.strftime('/%Y/%m/%d/', save_time.timetuple())

    # Check and create for directories
    complete_file_path = os.path.join(settings.MEDIA_ROOT, ('Graph/Survey' + path1))
    if not os.path.exists(complete_file_path):
        os.makedirs(complete_file_path)

    file_name = str(survey.uuid)

    survey_account = survey.surveyaccount

    cost = survey_account.survey_cost
    featured = False
    error_meta = {}

    caught_exception = False

    graph = SurveyGraph(money=cost, featured=featured)
    try:
        max_coin = graph.generate_model()
    except AssertionError:
        caught_exception = True
        error_meta = graph.error_meta
        survey.check_flag = False
        survey.save()
        raise GraphError('Survey graph creation Failed')
    except:
        caught_exception = True
        error_meta = graph.error_meta
        error_meta.update({"ERROR": "Unknown Error, probably memory error"})
        survey.check_flag = False
        survey.save()
        raise GraphError('Unknown Error, Please check Error Log')
    else:
        try:
            with transaction.atomic():
                error_meta = graph.error_meta
                survey.max_coins = max_coin

                file_location = 'Graph/Survey' + path1 + (file_name + '.png')

                complete_file_location = os.path.join(settings.MEDIA_ROOT, ('Graph/Survey' + path1),
                                                      (file_name + '.png'))

                graph.plot_graph(complete_file_location, file_name)

                survey_account.max_fill = graph.people
                survey.save()
                graph_obj = Graph.objects.create(graph_model=graph.model_dict,
                                                 graph_user=graph.user_dict, user_pos=graph.user_pos_dict,
                                                 stats=graph.stats, graph_file=file_location)
                survey_account.graph_id = graph_obj
                survey_account.save()
        except Exception:
            caught_exception = True
            error_meta = graph.error_meta
            error_meta.update({"ERROR": "Unknown Error in transaction.atomic block, probably django SQL memory error"})
            survey.check_flag = False
            survey.save()
            raise GraphError('Unknown Error, Please check Error Log')
    finally:
        if caught_exception or bool(error_meta):
            error_meta.update({"survey_id": str(survey.id)})
            ErrorLog.objects.create(error_code=300, error_type="Graph_Error", error_meta=error_meta, actor=user)


def test_state_video(video, curr_state):
    error_meta = {}
    jump_over = False
    previous_state = VideoState.objects.get(video_id=video, active_head=True)
    if previous_state.current != curr_state:
        if previous_state.current == 'FT':
            return {}, False, True
        else:
            error_meta.update({"ERROR": "VideoStateError",
                               "VideoState": previous_state.current})
            jump_over = True

    if not jump_over:
        video.create_state(
            previous_state, 'EG',
            {"error_message": "System Error, Please raise a ticket if any action isn't taken"}
        )
    return error_meta, jump_over, False
