import collections
from datetime import datetime as dt
from datetime import timedelta
import matplotlib.pyplot as plt

from modularodm import Q

from website.app import init_app
from website.models import NodeLog, User

color_map = {
    'comments': 'red',
    'wiki': 'skyblue',
    'registrations': 'lime',
    'nodes': 'yellow',
    'files': 'magenta'
}

def last_week():
    now = dt.utcnow()
    return [now - timedelta(days=i) for i in range(0,6)]

def build_time_query(end):
    return Q('date', 'gt', end - timedelta(days=1)) & Q('date', 'lt', end)

def order_users_get():
    us = User.find()
    points = {u.get_activity_points: u for u in us}
    ordered = collections.OrderedDict(sorted(points.items()))
    ordered = ordered.values()
    l = len(ordered)
    return ordered[0:3], ordered[int(l/3), int(l/3)+3], ordered[int(l/1.5), int(l/1.5) + 3]

def get_agg_for_user(user, date):
    return {
        'comments': len(list(NodeLog.find(Q('user', 'eq', user) & Q('action', 'eq', NodeLog.COMMENT_ADDED) & build_time_query(date)))),
        'wiki': len(list(NodeLog.find(Q('user', 'eq', user) & Q('action', 'eq', NodeLog.WIKI_UPDATED) & build_time_query(date)))),
        'registrations': len(list(NodeLog.find(Q('user', 'eq', user) & Q('action', 'eq', NodeLog.PROJECT_REGISTERED) & build_time_query(date)))),
        'nodes': len(list(NodeLog.find(Q('user', 'eq', user) & (Q('action', 'eq', NodeLog.PROJECT_CREATED) | Q('action', 'eq', NodeLog.NODE_CREATED)) & build_time_query(date)))),
        'files': len(list(NodeLog.find(Q('user', 'eq', user) & (Q('action', 'eq', NodeLog.FILE_ADDED) | Q('action', 'eq', NodeLog.FILE_UPDATED)) & build_time_query(date)))),
    }


def main():
    top, mid, bot = order_users_get()
    days_in_last_week = last_week()
    top_agg = {str(day): {} for day in days_in_last_week}
    mid_agg = {str(day): {} for day in days_in_last_week}
    bot_agg = {str(day): {} for day in days_in_last_week}
    aggs = [(top, top_agg), (mid, mid_agg), (bot, bot_agg)]
    for sample, agg in aggs:
        for user in sample:
            for day in days_in_last_week:
                data = get_agg_for_user(user, day)
                agg.update(
                    {
                        str(day): {key: val + (agg[str(day)].get(key) or 0) for key, val in data.iteritems()}}
                )
        agg.update(
            {key: {k: v/3 for k, v in val.iteritems()} for key, val in agg.iteritems()}
        )
    days = [1, 2, 3, 4, 5, 6]
    days_map, junk = top_agg.iteritems()
    plt.figure(1)
    plt.subplot(211)
    plt.ylabel('Number of events')
    plt.xlabel('Day of the week')
    plt.title('Top users (100%)')
    plt.plot(days, [top_agg[day].get('commments') for day in days_map], color_map['comments'],
             days, [top_agg[day].get('wiki') for day in days_map], color_map['wiki'],
             days, [top_agg[day].get('registrations') for day in days_map], color_map['registrations'],
             days, [top_agg[day].get('nodes') for day in days_map], color_map['nodes'],
             days, [top_agg[day].get('files') for day in days_map], color_map['files'],
             )
    plt.subplot(212)
    plt.ylabel('Number of events')
    plt.xlabel('Day of the week')
    plt.title('Middle users (66%)')
    plt.plot(days, [mid_agg[day].get('commments') for day in days_map], color_map['comments'],
             days, [mid_agg[day].get('wiki') for day in days_map], color_map['wiki'],
             days, [mid_agg[day].get('registrations') for day in days_map], color_map['registrations'],
             days, [mid_agg[day].get('nodes') for day in days_map], color_map['nodes'],
             days, [mid_agg[day].get('files') for day in days_map], color_map['files'],
             )
    plt.subplot(213)
    plt.ylabel('Number of events')
    plt.xlabel('Day of the week')
    plt.title('Bottom users (33%)')
    plt.plot(days, [bot_agg[day].get('commments') for day in days_map], color_map['comments'],
             days, [bot_agg[day].get('wiki') for day in days_map], color_map['wiki'],
             days, [bot_agg[day].get('registrations') for day in days_map], color_map['registrations'],
             days, [bot_agg[day].get('nodes') for day in days_map], color_map['nodes'],
             days, [bot_agg[day].get('files') for day in days_map], color_map['files'],
             )
    plt.show()


if __name__ == '__main__':
    init_app()
    main()
