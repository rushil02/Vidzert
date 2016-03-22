import subprocess


def check_video_inst(input_video):
    # input_video = settings.MEDIA_ROOT + '/' + video_file.video_file_orig.name

    # uuid_str = str(video_file.video_id.uuid)

    error_msg2 = 'Audio stream is not present or is of unrecognised codec'
    error_msg3 = 'Video stream is not present or is of unrecognised codec'
    error_msg4 = 'Height of the video is too Low, revise the resolution'
    error_msg5 = 'Width of the video is too Low, revise the resolution'
    error_msg6 = 'Portrait videos are not supported'

    # print "Check Initialized for video:", uuid_str
    try:
        size = subprocess.check_output(
            ['ffprobe', '-v', '-8', '-show_entries', 'format=size', '-i', input_video, '-of',
             'default=nk=1:nw=1'])
        size = int(size.strip() or 0)

        duration = subprocess.check_output(
            ['ffprobe', '-v', '-8', '-show_entries', 'format=duration', '-i', input_video, '-of',
             'default=nk=1:nw=1'])
        duration = float(duration.strip() or 0.0)

        audio_codec = subprocess.check_output(
            ['ffprobe', '-v', '-8', '-show_entries', 'stream=codec_name', '-select_streams', 'a', '-i', input_video,
             '-of', 'default=nk=1:nw=1'])
        audio_codec = audio_codec.strip()

        video_codec = subprocess.check_output(
            ['ffprobe', '-v', '-8', '-show_entries', 'stream=codec_name', '-select_streams', 'v', '-i', input_video,
             '-of', 'default=nk=1:nw=1'])
        video_codec = video_codec.strip()

        width = subprocess.check_output(
            ['ffprobe', '-v', '-8', '-show_entries', 'stream=width', '-i', input_video, '-of', 'default=nk=1:nw=1'])
        width = int(width.strip() or 0)

        height = subprocess.check_output(
            ['ffprobe', '-v', '-8', '-show_entries', 'stream=height', '-i', input_video, '-of', 'default=nk=1:nw=1'])
        height = int(height.strip() or 0)

    except subprocess.CalledProcessError:

        error = "File corrupt"
        return error, None
    else:
        error_list = []
        try:
            assert (size <= 104857600)  # less than or equal to 100 MB
        except AssertionError:
            error_list.append('Video should be less than or equal to 100MB')
        try:
            assert (7 <= duration <= 300)  # less than or equal to 5 minutes and greater than or equal to  7 seconds
        except AssertionError:
            error_list.append('Video should be less than or equal to 5 mins and greater than or equal to  7 seconds')
        try:
            assert (audio_codec is not None)
        except AssertionError:
            error_list.append(error_msg2)
        try:
            assert (video_codec is not None)
        except AssertionError:
            error_list.append(error_msg3)
        try:
            assert (height >= 480)
        except AssertionError:
            error_list.append(error_msg4)
        try:
            assert (width >= 640)
        except AssertionError:
            error_list.append(error_msg5)
        try:
            assert (width > height)
        except AssertionError:
            error_list.append(error_msg6)

        # print "Task Complete for video:", uuid_str

        if error_list:
            return "Validation errors", error_list
        else:
            return "No Errors", None
