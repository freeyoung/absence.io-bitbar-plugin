#!/usr/local/bin/python3
import os
import sys
import json
import logging
import requests
import configparser
from mohawk import Sender
from datetime import datetime, date
from dateutil import parser, tz, relativedelta

CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.absence.cfg')

if not os.path.exists(CONFIG_FILE):
    print(f'{CONFIG_FILE} does not exist')
    exit(1)

CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_FILE)
USER_ID = CONFIG['absence']['user_id']
USER_KEY = CONFIG['absence']['user_key']

PAGE_SIZE = 100
EXEC_SELF = sys.argv[0]

WORKING_SYMBOL = (
    ':black_medium_square:',
    ':arrow_forward:',
)


def local_now():
    return datetime.now(tz.tzlocal())


def utc_now():
    return datetime.now(tz.UTC)


def absence_ftime(dt):
    if isinstance(dt, datetime):
        return f'{dt.strftime("%Y-%m-%dT%H:%M:%S")}.{int(dt.microsecond / 1000):03d}Z'
    elif isinstance(dt, date):
        return dt.strftime('%Y-%m-%d')
    return dt


def query_absence_api(endpoint, data, method='POST'):
    url = f'https://app.absence.io/api/v2{endpoint}'
    content = json.dumps(data)
    content_type = 'application/json'

    sender = Sender({
        'id': USER_ID,
        'key': USER_KEY,
        'algorithm': 'sha256'
    },
                    url,
                    method,
                    content=content,
                    content_type=content_type)

    response = getattr(requests, method.lower())(
        url,
        data=content,
        headers={
            'Authorization': sender.request_header,
            'Content-Type': content_type
        })
    return response


def get_timespans_from(start):
    data = {
        "filter": {
            "userId": USER_ID,
            "start": {
                "$gte": absence_ftime(start),
            },
        },
        "type": "work",
        "limit": PAGE_SIZE,
        "skip": 0
    }
    response = query_absence_api('/timespans', data)
    timespans = response.json()['data']
    return timespans


def sum_total_working_hours_and_minutes_from(timespans):
    seconds = 0
    for timespan in timespans:
        seconds += (parser.parse(
            timespan.get('effectiveEnd',
                         local_now().isoformat())) - parser.parse(
                             timespan['effectiveStart'])).seconds
    total = relativedelta.relativedelta(seconds=seconds)
    return f'{total.days * 24 + total.hours:02d}h {total.minutes:02d}m'


def check_working(timespans):
    if not timespans:
        return False
    return 'effectiveEnd' not in timespans[-1]


def start_working():
    data = {
        "userId": USER_ID,
        "start": absence_ftime(utc_now()),
        "timezoneName": local_now().strftime('%Z'),
        "timezone": local_now().strftime('%z'),
        "end": None,
        "type": "work"
    }
    response = query_absence_api('/timespans/create', data)
    return response.ok


def stop_working():
    last_timespan = timespans_today[-1]
    data = {
        "start": last_timespan['start'],
        "end": absence_ftime(utc_now()),
        "timezoneName": local_now().strftime('%Z'),
        "timezone": local_now().strftime('%z')
    }
    response = query_absence_api(f'/timespans/{last_timespan["_id"]}', data,
                                 'PUT')
    return response.ok


if __name__ == '__main__':
    action = None
    if len(sys.argv) > 1:
        action = sys.argv[1]

    today = local_now().date()

    timespans_today = get_timespans_from(today)
    is_working = check_working(timespans_today)

    if action == 'start' and not is_working:
        start_working()
    elif action == 'stop' and is_working:
        stop_working()

    hours_minutes = sum_total_working_hours_and_minutes_from(timespans_today)
    symbol = WORKING_SYMBOL[is_working]
    print(f'{symbol} {hours_minutes}')

    print('---')
    if is_working:
        print(
            f'Stop Working | bash={EXEC_SELF} param1=stop terminal=false refresh=true'
        )
    else:
        print(
            f'Start Working | bash={EXEC_SELF} param1=start terminal=false refresh=true'
        )

    print('---')
    print(f'Today = {hours_minutes}')

    for timespan in reversed(timespans_today):
        start = parser.parse(timespan['effectiveStart']).astimezone(
            tz.tzlocal()).strftime('%H:%M')
        end = parser.parse(
            timespan.get('effectiveEnd',
                         utc_now().isoformat())).astimezone(
                             tz.tzlocal()).strftime('%H:%M')
        total = sum_total_working_hours_and_minutes_from([timespan])
        line = f'-- {start} ~ {end} = {total} | font=Menlo'
        if 'effectiveEnd' not in timespan:
            line += ' color=green'
        print(line)

    print('---')
    monday = today - relativedelta.relativedelta(days=today.weekday())
    hours_minutes = sum_total_working_hours_and_minutes_from(
        get_timespans_from(monday))
    print(f'This week = {hours_minutes}')

    first_day_of_month = today.replace(day=1)
    hours_minutes = sum_total_working_hours_and_minutes_from(
        get_timespans_from(first_day_of_month))
    print(f'This month = {hours_minutes}')

    print('---')
    print('Go to Absence.io | href=https://app.absence.io/#/timetracking')
