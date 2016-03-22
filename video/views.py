from django.shortcuts import render
import time
from perks.models import Perks


# Create your views here.


def watch(request, video, promoter_uuid=None):
    video_info = video.videoinfo
    pre_perk = None
    post_perk = None
    position = None
    quantity = None
    delete_session_data(request)
    if request.POST:
        pre_perk_uuid = request.POST.get('pre_perk')
        post_perk_uuid = request.POST.get('post_perk')
        position = request.POST.get('position')
        quantity = request.POST.get('quantity')
        if pre_perk_uuid is None or pre_perk_uuid == "None":
            pre_perk = None
        else:
            pre_perk = Perks.objects.get_perk(pre_perk_uuid)
            request.session['pre_perk_id'] = pre_perk.perk_id
            request.session['position'] = position
            request.session['quantity'] = quantity

        if post_perk_uuid is None or post_perk_uuid == "None":
            post_perk = None
        else:
            post_perk = Perks.objects.get_perk(post_perk_uuid)
            request.session['post_perk_id'] = post_perk.perk_id

    request.session['video_id'] = video.id
    request.session['video_duration'] = str(video.videofile.video_duration)
    request.session['start_time'] = time.time()

    if promoter_uuid:
        request.session['promoter_uuid'] = promoter_uuid

    context = {
        "video": video,
        "pre_perk": pre_perk,
        "post_perk": post_perk,
        "video_info": video_info,
        "promoter_uuid": promoter_uuid,
        "position": position,
        "quantity": quantity
    }
    return render(request, 'video/playback.html', context)


def delete_session_data(request):
    request.session.pop('pre_perk_id', None)
    request.session.pop('position', None)
    request.session.pop('quantity', None)
    request.session.pop('post_perk_id', None)
    request.session.pop('video_id', None)
    request.session.pop('video_duration', None)
    request.session.pop('start_time', None)
    request.session.pop('promoter_uuid', None)
