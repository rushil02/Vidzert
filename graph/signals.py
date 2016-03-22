# from django.dispatch import receiver
#
# from .tasks import video_graph_async, survey_graph_async
# from survey.models import SurveyAccount
# from video.models import VideoFile
# from django.contrib.auth import get_user_model
#
#
# # @receiver(create_graph, sender=VideoFile)
# def create_video_graph_model(sender, **kwargs):
#     video_file = kwargs.get('instance')
#     video = video_file.video_id
#     if not video.videoaccount.graph_id:
#         client_user = get_user_model().objects.get(clientprofile__video__videofile=video_file)
#         video_graph_async.apply_async((video.id, client_user.id, True), countdown=2)
#
#
# # @receiver(create_graph, sender=SurveyAccount)
# def create_survey_graph_model(sender, **kwargs):
#     survey_account = kwargs.get('instance')
#     survey = survey_account.survey_id
#     if not survey.check_flag:
#         return
#     else:
#         if kwargs.get('force_create', False) or (not survey_account.graph_id):
#             client_user = get_user_model().objects.get(clientprofile__survey__surveyaccount=survey_account)
#             survey_graph_async.apply_async((survey.id, client_user.id), countdown=2)
