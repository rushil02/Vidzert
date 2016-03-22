from django.shortcuts import render
from models import Perks
from django.db.models import F


# Create your views here.
def double_up(perk, coins):
    perk.increment_times_used()
    return 2*coins


def magnet(perk, graph, position):
    (pre_user_graph_position, pre_coins) = graph.get_pos(position-1)
    (curr_user_graph_position, curr_coins) = graph.get_pos(position)
    (post_user_graph_position, post_coins) = graph.get_pos(position+1)
    curr_coins += pre_coins
    curr_coins += post_coins
    perk.increment_times_used()
    return curr_coins


def position_wildcard(perk, graph, position, quantity=1):
    perk.increment_times_used(quantity)
    (x_data, y_data, coins) = graph.get_pos(position)
    return x_data, y_data, coins


def time_wildcard(perk, graph, video, time):
    promoter_log = video.videopromoterlog_set.filter(create_time__gte=time)[0]
    unsubscribed_log = video.videounsubscribedlog_set.filter(create_time__gte=time, position__isnull=False)[0]

    if promoter_log and unsubscribed_log:
        if promoter_log.position > unsubscribed_log.position:
            position = promoter_log.position
        else:
            position = unsubscribed_log.position
    elif promoter_log:
        position = promoter_log.position
    elif unsubscribed_log:
        position = unsubscribed_log.position
    else:
        print "Wrong Time Entered"
        position = -1

    (user_graph_position, curr_coins) = graph.get_pos(position)
    perk.increment_times_used()
    return user_graph_position, curr_coins
