# from django.dispatch import receiver
# from .tasks import create_thumbnail_async, secure_conv_video, set_duration
#
# from .models import VideoFile
# from django.contrib.auth import get_user_model
# # from video.dispatcher import secure_convert_meta
#
#
# # @receiver(secure_convert_meta, sender=VideoFile)
# def convert_video(sender, **kwargs):
#     video_file = kwargs.get('instance')
#     video = video_file.video_id
#     client_user = get_user_model().objects.get(clientprofile__video=video)
#
#     if video_file.thumbnail_image:
#         (secure_conv_video.si(
#             video.id, client_user.id, True,
#         ) | set_duration.si(
#             video.id, client_user.id, True
#         )).apply_async(countdown=2)
#     else:
#         (secure_conv_video.si(
#             video.id, client_user.id, True,
#         ) | create_thumbnail_async.si(
#             video.id, client_user.id, True
#         ) | set_duration.si(
#             video.id, client_user.id, True
#         )).apply_async(countdown=2)
