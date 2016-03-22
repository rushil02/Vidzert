from __future__ import absolute_import

import os
import subprocess

from django.conf import settings
from Vidzert.celery import app
from admin_custom.custom_errors import VideoError, VideoStateError, ForceTerminate
from video.models import Video, VideoState
from admin_custom.models import ErrorLog
from django.contrib.auth import get_user_model


@app.task(name='create_thumbnail', throws=(VideoError, VideoStateError, ForceTerminate))
def create_thumbnail_async(video_id, client_user_id, video_state_aware=True, curr_state='VU'):
    video = Video.objects.select_related('videofile').get(id=video_id)
    video_file = video.videofile
    user = get_user_model().objects.get(id=client_user_id)

    if video_state_aware:
        previous_state = video.get_previous_state()
        if previous_state.current != curr_state:
            if previous_state.current == 'FT':
                raise ForceTerminate
            else:
                error_meta = ({"video_id": str(video.id), "method": "video.tasks.create_thumbnail_async",
                               "VideoState": previous_state.current})
                ErrorLog.objects.create(error_code=300, error_type="VideoStateError", error_meta=error_meta, actor=user)
                raise VideoStateError

    # check for 'Thumbnails' directory
    file_path_thumbnail = settings.MEDIA_ROOT + '/' + os.path.dirname(
        os.path.dirname(video_file.video_file_orig.name)) + '/Thumbnails'
    if not os.path.exists(file_path_thumbnail):
        os.makedirs(file_path_thumbnail)

    # set path
    video_file_name = settings.MEDIA_ROOT + '/' + video_file.video_file_orig.name
    uuid_str = str(video_file.video_id.uuid)
    image_path = os.path.dirname(os.path.dirname(video_file.video_file_orig.name)) + '/Thumbnails/' + uuid_str + '.png'

    image_absolute_location = settings.MEDIA_ROOT + '/' + image_path

    jump_over = False

    error_meta = {}

    try:
        subprocess.check_output(['ffmpeg', '-v', '-8', '-i', video_file_name, '-vframes', '1',
                                 '-an', '-s', '858x480', '-ss', '5', image_absolute_location,
                                 '-y'])  # TODO: size of image?

    except subprocess.CalledProcessError:
        if video_state_aware:
            error_meta, jump_over, marker = test_state_video(video, curr_state)
            if marker:
                raise ForceTerminate

        if not jump_over:
            error_meta = {'video_object_id': str(video_file.video_id.id),
                          'video_uuid': uuid_str}
            ErrorLog.objects.create(error_code=6625, error_type="Create_Thumbnail_Error", error_meta=error_meta,
                                    actor=user)
            raise VideoError('Create thumbnail Failed, file not recognised by FFmpeg')
        else:
            error_meta.update({'video_object_id': str(video_file.video_id.id),
                               'video_uuid': uuid_str})
            ErrorLog.objects.create(error_code=6621, error_type="VideoStateError", error_meta=error_meta,
                                    actor=user)
            raise VideoStateError
    else:
        video_file.thumbnail_image.name = image_path
        video_file.save()


@app.task(name='Secure_convert_video', throws=(VideoError, VideoStateError, ForceTerminate))
def secure_conv_video(video_id, client_user_id, video_state_aware=True, curr_state='VU'):
    video = Video.objects.select_related('videofile').get(id=video_id)
    video_file = video.videofile
    user = get_user_model().objects.get(id=client_user_id)

    if video_state_aware:
        previous_state = video.get_previous_state()
        if previous_state.current != curr_state:
            if previous_state.current == 'FT':
                raise ForceTerminate
            else:
                error_meta = ({"video_id": str(video.id), "method": "video.tasks.secure_conv_video",
                               "VideoState": previous_state.current})
                ErrorLog.objects.create(error_code=300, error_type="VideoStateError", error_meta=error_meta, actor=user)
                raise VideoStateError

    print "Setting file path"
    # Check and create for directories
    file_path_mp4 = settings.MEDIA_ROOT + '/' + os.path.dirname(
        os.path.dirname(video_file.video_file_orig.name)) + '/Mp4'
    if not os.path.exists(file_path_mp4):
        os.makedirs(file_path_mp4)

    file_path_webm = settings.MEDIA_ROOT + '/' + os.path.dirname(
        os.path.dirname(video_file.video_file_orig.name)) + '/Webm'
    if not os.path.exists(file_path_webm):
        os.makedirs(file_path_webm)

    # Set path
    input_video = settings.MEDIA_ROOT + '/' + video_file.video_file_orig.name
    uuid_str = str(video_file.video_id.uuid)

    mp4_path = os.path.dirname(os.path.dirname(video_file.video_file_orig.name)) + '/Mp4/' + uuid_str + '.mp4'

    webm_path = os.path.dirname(os.path.dirname(video_file.video_file_orig.name)) + '/Webm/' + uuid_str + '.webm'

    output_video_mp4 = settings.MEDIA_ROOT + '/' + mp4_path
    output_video_webm = settings.MEDIA_ROOT + '/' + webm_path

    jump_over = False

    error_meta = {}

    print "Secure convert Initialized for", uuid_str

    try:  # Security check
        # Check every video frame header
        print "Security check - Pass1: Processing " + uuid_str
        subprocess.check_output(['ffprobe', '-v', '-8', '-show_frames', '-i', input_video])
        print "Security check - Pass1: Complete " + uuid_str

        # Check via decoding video
        print "Security check - Pass2: Processing " + uuid_str
        subprocess.check_call(['ffmpeg', '-v', '-8', '-i', input_video, '-f', 'null', '-'])
        print "Security check - Pass2: Complete " + uuid_str

    except subprocess.CalledProcessError:
        if video_state_aware:
            error_meta, jump_over, marker = test_state_video(video, curr_state)
            if marker:
                raise ForceTerminate

        if not jump_over:
            error_meta = {'video_object_id': str(video_file.video_id.id),
                          'video_uuid': uuid_str}
            ErrorLog.objects.create(error_code=6626, error_type="Security check Failed", error_meta=error_meta,
                                    actor=user)
        else:
            error_meta.update({'video_object_id': str(video_file.video_id.id),
                               'video_uuid': uuid_str})
            ErrorLog.objects.create(error_code=6621, error_type="VideoStateError", error_meta=error_meta,
                                    actor=user)
            raise VideoStateError

        raise VideoError('Security Checks Failed')

    else:

        try:  # Start conversion

            # convert to 480p, preserve aspect ratio, h264 - libx264 video codec,
            # aac - native experimental aac audio codec, mp4 container, max bitrate 500kbps at content ratio:20,
            # 25 framerate
            print "Converting to mp4: " + uuid_str
            subprocess.check_call(
                ['ffmpeg', '-v', '-8', '-i', input_video, '-vf', 'scale=-2:480', '-preset', 'slow',
                 '-c:v', 'libx264', '-strict', 'experimental', '-c:a', 'aac', '-crf', '20', '-maxrate', '500k',
                 '-bufsize', '500k', '-r', '25', '-f', 'mp4', output_video_mp4, '-y'])
            print "Conversion complete: " + uuid_str

            # convert to 360p, preserve aspect ratio, vp8 - libvpx video codec, vorbis - libvorbis audio codec,
            # webm container, max bitrate 300kbps at content ratio:8, 25 framerate
            print "Converting to webm: " + uuid_str
            subprocess.check_call(
                ['ffmpeg', '-v', '-8', '-i', input_video, '-vf', 'scale=-2:360', '-quality', 'good',
                 '-cpu-used', '1', '-c:v', 'libvpx', '-c:a', 'libvorbis', '-crf', '8', '-maxrate', '300k',
                 '-bufsize', '300k', '-r', '25', '-f', 'webm', output_video_webm, '-y'])
            print "Conversion complete: " + uuid_str

        except subprocess.CalledProcessError:
            if video_state_aware:
                error_meta, jump_over, marker = test_state_video(video, curr_state)
                if marker:
                    raise ForceTerminate

            if not jump_over:
                error_meta = {'video_object_id': str(video_file.video_id.id),
                              'video_uuid': uuid_str}
                ErrorLog.objects.create(error_code=6627, error_type="Conversion Failed", error_meta=error_meta,
                                        actor=user)
                raise VideoError('Create thumbnail Failed, file not recognised by FFmpeg')
            else:
                error_meta.update({'video_object_id': str(video_file.video_id.id),
                                   'video_uuid': uuid_str})
                ErrorLog.objects.create(error_code=6621, error_type="VideoStateError", error_meta=error_meta,
                                        actor=user)
                raise VideoStateError

        else:
            video_file.video_file_mp4.name = mp4_path
            video_file.video_file_webm.name = webm_path
            video_file.save()


@app.task(name='Extract_and_set_video_duration', throws=(VideoError, VideoStateError, ForceTerminate))
def set_duration(video_id, client_user_id, video_state_aware=True, curr_state='VU', nxt_state='VC'):
    video = Video.objects.select_related('videofile').get(id=video_id)
    video_file = video.videofile
    user = get_user_model().objects.get(id=client_user_id)

    if video_state_aware:
        previous_state = video.get_previous_state()
        if previous_state.current != curr_state:
            if previous_state.current == 'FT':
                raise ForceTerminate
            else:
                error_meta = ({"video_id": str(video.id), "method": "video.tasks.set_duration",
                               "VideoState": previous_state.current})
                ErrorLog.objects.create(error_code=300, error_type="VideoStateError", error_meta=error_meta, actor=user)
                raise VideoStateError

    filename = settings.MEDIA_ROOT + '/' + video_file.video_file_orig.name

    jump_over = False

    error_meta = {}

    try:
        duration = subprocess.check_output(['ffprobe', '-i', filename, '-show_entries',
                                            'format=duration', '-v', '-8', '-of', 'default=nk=1:nw=1'])
        duration = float(duration.strip())
    except subprocess.CalledProcessError:
        if video_state_aware:
            error_meta, jump_over, marker = test_state_video(video, curr_state)
            if marker:
                raise ForceTerminate

        if not jump_over:
            error_meta = {'video_object_id': str(video_file.video_id.id),
                          'video_uuid': str(video_file.video_id.uuid)}
            ErrorLog.objects.create(error_code=6625, error_type="Extract duration failed", error_meta=error_meta,
                                    actor=user)
            raise VideoError('Create thumbnail Failed, file not recognised by FFmpeg')
        else:
            error_meta.update({'video_object_id': str(video_file.video_id.id),
                               'video_uuid': str(video_file.video_id.uuid)})
            ErrorLog.objects.create(error_code=6621, error_type="VideoStateError", error_meta=error_meta,
                                    actor=user)
            raise VideoStateError

    else:
        video_file.video_duration = duration
        video_file.save()

        if video_state_aware:
            previous_state = video.get_previous_state()
            if previous_state.current == 'FT':
                raise ForceTerminate
            elif previous_state.current == curr_state:
                video.create_state(previous_state, nxt_state)
            else:
                error_meta.update({'video_object_id': str(video_file.video_id.id),
                                   'video_uuid': str(video_file.video_id.uuid),
                                   "method": "video.tasks.set_duration",
                                   'VideoState': previous_state.current})
                ErrorLog.objects.create(error_code=6621, error_type="VideoStateError", error_meta=error_meta,
                                        actor=user)
                raise VideoStateError


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
            previous_state, 'EC', {"message": "Security checks failed on video."}
        )

    return error_meta, jump_over, False
