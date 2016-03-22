from models import VideoCompletionLog
from video.models import Video
from promoter.models import PromoterProfile
from logs.models import VideoUnsubscribedLog, VideoPromoterLog
import pygeoip
import os
from django.conf import settings
from collections import Counter
import copy
import math
import time


# Global settings

# Geo-location relational to IP data
gi = settings.GI

# Home locations for a user settings
PAST_LOG_LENGTH = 1000
NUMBER_OF_HOME_STATES = 2
HOMES = {}

# Add parameters here with their half_life and Max_weight
ID_METHODS = ['IP', 'FP']

# Half-life (time at which probability of second occurrence or weight will be half of original) in hours
HALF_LIFE = {'IP': 24.0,
             'FP': 24.0,
             }

# Half-life 2 (cont. iteration at which weight will be half of original)
HALF_LIFE_2 = {'IP': 24,  # TODO
               'FP': 24,
               'USER': 24,
               }

HALF_LIFE_USER_PENALTY = 50

MAX_WEIGHT = {'IP': 1.0,
              'FP': 1.0,
              }

ENGAGEMENT_THRESHOLD = 0.1


def collect_data():
    videos = Video.objects.filter(videocompletionlog__verified='Q')
    promoters = PromoterProfile.objects.filter(videopromoterlog__video_id__in=videos) \
        .distinct('videopromoterlog__promoter_id')
    return videos, promoters


def collect_backlink_viewers(promoter, videos):
    backlink_viewers = VideoUnsubscribedLog.objects.filter(promoter_id=promoter, video_id__in=videos)
    return backlink_viewers


def collect_anonymous_viewers(videos):
    anonymous_viewers = VideoUnsubscribedLog.objects.filter(video_id__in=videos, promoter_id__isnull=True)
    return anonymous_viewers


def check_proxy(ip):
    return False


def compare_characteristics(view1, view2):  # TODO: add if conditions according to parameters
    count = 0
    checks_dict = {}
    for ch in ID_METHODS:
        checks_dict[ch] = False

    if view1.ip == view2.ip:
        count += 1
        checks_dict['IP'] = True

    if view1.fp == view2.fp:
        count += 1
        checks_dict['FP'] = True
    return checks_dict, count


def cal_decay(w, time1, time2, half_life):
    if time1 > time2:
        decay_time = ((time1 - time2).total_seconds()) / 3600  # time in hours
    else:
        decay_time = ((time2 - time1).total_seconds()) / 3600  # time in hours

    try:
        if decay_time <= half_life:
            cal_weight = ((w / 2) * math.cos(decay_time / (2 * half_life / math.pi))) + \
                         w / 2
        else:
            cal_weight = w / math.exp(math.log(2) * decay_time / half_life)
    except:
        return 1.0
    else:
        return cal_weight


def cal_decay_2(w, decay_num, half_life):

    try:
        assert decay_num >= 0

        if decay_num <= half_life:
            cal_weight = ((w / 2) * math.cos(decay_num / (2 * half_life / math.pi))) + \
                         w / 2
        else:
            cal_weight = w / math.exp(math.log(2) * decay_num / half_life)
    except:
        return 1.0
    else:
        return cal_weight


# def cal_user_penalty(promoter):
#     # Fetch count of entries in log (with positively checked backlinks) since last change in
#     # penalty value and decay it using cal_value_2
#     count = 50.0
#     # Fetch stored user penalty
#     penalty = 50.0
#     try:
#         decayed_penalty = cal_decay_2(penalty, count, HALF_LIFE_USER_PENALTY)
#     except:
#         return 0.0
#     else:
#         return decayed_penalty


def mark_roll_back(roll_back_list):
    # TODO: write queryset to mark for rollback given list entries
    pass


# def get_home_location(promoter):
#     if HOMES:
#         return HOMES
#     else:
#         global HOMES
#         promoter_log = PromoterLog.objects.filter(promoter_id=promoter)  # TODO: get PAST_LOG_LENGTH entries or so only
#         promoter_ip_location = []
#         for log_entry in promoter_log:
#             try:
#                 if check_proxy(log_entry.ip) is False:
#                     location = gi.record_by_addr(log_entry.ip)  # TODO: location query, get location code
#                     if location == '':
#                         raise Exception
#             except:
#                 continue
#
#             promoter_ip_location.append(gi.record_by_addr(str(log_entry.ip)))
#
#         homes = Counter(promoter_ip_location).most_common(NUMBER_OF_HOME_STATES)
#
#         for home in homes:  # Confidence Values
#             homes[home] = float(homes[home]) / PAST_LOG_LENGTH
#         HOMES = copy.deepcopy(homes)
#         return HOMES


def same_user_in_timeframe(viewer_list, user_penalty):
    roll_back_list = []  # stores only list of primary keys
    weight = {}
    weight_2 = {}
    local_penalty = {}
    ref_time = {}
    decay_num = Counter()
    local_penalty_2 = {}
    new_user_penalty = 0.0
    i = 0

    for view in viewer_list:
        i += 1
        if view in roll_back_list:
            continue
        else:
            local_penalty.clear()
            local_penalty_2.clear()
            ref_time.clear()
            for ch in ID_METHODS:
                local_penalty[ch] = user_penalty
                ref_time[ch] = view.create_time
                decay_num[ch] = 0
                local_penalty_2[ch] = user_penalty
            marker = False

            for another_view in viewer_list:
                decay_num.update(decay_num.keys())
                    
                if view is another_view:
                    continue
                else:
                    checks_dict, count = compare_characteristics(view, another_view)
                    if count > 0:
                        
                        weight.clear()
                        weight_2.clear()

                        for check_type in checks_dict:
                            if checks_dict[check_type]:

                                w1 = MAX_WEIGHT[check_type] + local_penalty[check_type]
                                weight[check_type] = cal_decay(w1, ref_time[check_type], another_view.create_time,
                                                               HALF_LIFE[check_type])

                                w2 = MAX_WEIGHT[check_type] + local_penalty_2[check_type]
                                weight_2[check_type] = cal_decay_2(w2, decay_num[check_type]-1, HALF_LIFE_2[check_type])

                                local_penalty[check_type] = weight[check_type]
                                local_penalty_2[check_type] = weight_2[check_type]
                                ref_time[check_type] = another_view.create_time
                                decay_num[check_type] = 0

                        net_weight = (sum(weight.itervalues()) / count)
                        net_weight_2 = (sum(weight_2.itervalues()) / count)
                        max_net = max(net_weight, net_weight_2)
                        new_user_penalty += max_net

                        if another_view.pk not in roll_back_list:
                            if max_net >= 0.5:  # TODO: Add log entries meta data etc
                                marker = True
                                roll_back_list.append(another_view.pk)
                    
                    elif count is 0:
                        decay_num += 1

            if marker:
                roll_back_list.append(view.pk)

    new_user_penalty = new_user_penalty/i

    return roll_back_list, new_user_penalty


# def diverse_ip(viewer_list, promoter):  # TODO:Queryset to return counter values by IP
#     promoter_home = get_home_location(promoter)
#     location_dict = Counter()
#     for view in viewer_list:
#         try:
#             record_region = gi.record_by_addr(view.ip)['region_code']
#             assert record_region is None  # TODO
#         except AssertionError:
#             record_region = gi.record_by_addr(view.ip)['metro_code']
#         finally:
#             if record_region in location_dict:
#                 location_dict[record_region] += 1
#             else:
#                 location_dict.update({record_region: 1})


def engagement(viewer_list, promoter, video):
    i = 0
    j = 0
    for view in viewer_list:
        i += 1
        if view.ad_clicked:
            j += 1
    w = j/i
    if w >= ENGAGEMENT_THRESHOLD:
        return True, w  # USER Authenticated
    else:
        return False, w


def history(promoter, videos):
    weight = 0

    for video in videos:
        maxcount = 0
        count = 0
        weight += (maxcount / count) / 100

    return weight


def runtime(viewer_list):
    pass


def main_analyse(promoter, videos):
    backlink_list = collect_backlink_viewers(promoter, videos)

    user_penalty = 0

    diverse_ip(backlink_list, promoter)

    same_user_in_timeframe(backlink_list, user_penalty)


def main_method():
    videos, promoters = collect_data()

    for promoter in promoters:
        main_analyse(promoter, videos)


        # TODO: location from IP
        # gi = pygeoip.GeoIP(os.path.join(settings.BASE_DIR, "admin_custom", "data", "GeoLiteCity.dat"))
        # ip_city = gi.record_by_addr('122.180.235.254')
