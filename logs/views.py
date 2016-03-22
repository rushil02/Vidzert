from django.shortcuts import render
from models import VideoPromoterLog, VideoPromoterReplayLog, VideoUnsubscribedLog, \
    VideoPromoterPerkLog, PerkTransactionLog, DurationWatchedLog, GrayList, BlackList
from django.db.models import Q

# Create your views here.


# def promoter_log_entry(video, promoter, ip, share_url, coins, position, device_type):
#     log = VideoPromoterLog(video_id=video, promoter_id=promoter, ip=ip, share_url=share_url, coins=coins, position=position)
#     if device_type:
#         log.device_type = device_type
#     log.save()


# def replay_video_log_entry(video, promoter, ip, device_type):
#     log = VideoPromoterReplayLog(video_id=video, promoter_id=promoter, ip=ip)
#     if device_type:
#         log.device_type = device_type
#     log.save()


# def unsubsribed_log_entry(video, position, duration, promoter=None, ip=None, device_type=None, ad_clicked=False):
#     VideoUnsubscribedLog.objects.create(video_id=video, promoter_id=promoter, ip=ip, position=position, device_type=device_type, duration=duration, ad_clicked=ad_clicked)


# def video_promoter_perk_log_entry(video, promoter, perk, quantity=1):
#     VideoPromoterPerkLog.objects.create(video_id=video, promoter_id=promoter, perk_id=perk, quantity=quantity)


# def perk_transaction_log_entry(promoter, perk):
#     return PerkTransactionLog.objects.create(promoter_id=promoter, perk_id=perk, eggs=perk.cost)


# def duration_watch_log_entry(video, promoter, ip, duration, ad_clicked=False):
#     DurationWatchedLog.objects.create(video_id=video, promoter_id=promoter, ip=ip, duration=duration, ad_clicked=ad_clicked)


# def gray_list_entry(ip, promoter=None):
#     GrayList.objects.create(ip=ip, promoter_id=promoter)
#
#
# def black_list_entry(ip, promoter=None):
#     BlackList.objects.create(ip, promoter_id=promoter)