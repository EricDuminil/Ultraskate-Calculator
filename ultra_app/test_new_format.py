#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 10:11:14 2022

@author: ricou
"""
import requests
import requests_cache
import json
from datetime import timedelta, datetime
from dataclasses import dataclass

@dataclass
class Rider:
    id: int
    name: str
    team: str
    clydesdale: bool
    age: str
    discipline: str
    division: str
    time: str='0:00:00.00'
    laps: int = 0
    miles: float = 0.0
    kilometers: float = 0.0

requests_cache.install_cache('dev_cache', expire_after=timedelta(days=1))

EVENT_ID = '192607'

BASE_URL = "https://my.raceresult.com/RRPublish/data"

def get_json_data(url):
    print(f"### Downloading {url}")
    r = requests.get(url)
    return json.loads(r.content)

def get_key(event_id=EVENT_ID):
    url = f"{BASE_URL}/config.php?eventid={event_id}&page=live&noVisitor=1"
    return get_json_data(url)['key']

def get_live_results(event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/list.php?eventid={event_id}&key={key}&listname=Result+Lists%7COverall+Results+-+Live&page=live&contest=0&r=leaders&l=100"
    table = get_json_data(url)['data']
    categories = [cat for team_or_not in table.values() for cat in team_or_not.values()]
    riders = [rider for riders in categories for rider in riders if len(rider) > 1]
    return {int(id): (int(laps), time, float(miles.split(' ')[0])) for id, _a, _b, _name, _d, laps, miles, time, _diff in riders}

def get_laps(rider, event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/list.php?eventid={event_id}&key={key}&listname=Online%7CLap+Details&page=live&contest=0&r=bib2&bib={rider['id']}"
    return get_json_data(url)['data']

def get_participants(event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/list.php?eventid={event_id}&key={key}&listname=Participants%7CParticipants+List+123&page=participants&contest=0&r=all&l=0"
    return get_json_data(url)['data']

riders = []
for team_or_not, table in get_participants().items():
    for row in table:
        id, _id, _chip, name, team, clydesdale, age, discipline, division = row
        riders.append(Rider(int(id), name, team, clydesdale == 'Yes', age, discipline, division))

import pandas as pd
df = pd.DataFrame(riders)
df = df.set_index('id')
df = df.sort_index()

for id, (laps, time, miles) in get_live_results().items():
    df.at[id, 'laps'] = laps
    df.at[id, 'time'] = time
    df.at[id, 'miles'] = miles
    df.at[id, 'lap_length'] = miles / laps
    df.at[id, 'kilometers'] = round(miles * 1.609, 2)
    h, m, s = time.split(':')
    hours = float(h) + float(m) / 60 + float(s) / 3600
    # t = datetime.strptime(time,"%H:%M:%S.%f")
    # delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds = t.microsecond)
    # hours = delta / timedelta(hours=1)
    df.at[id, 'average_mph'] = round(miles / hours, 2)
    df.at[id, 'average_kph'] = round(miles * 1.609 / hours, 2)
    # df.loc[id]['laps'] = laps
    # df.loc[id]['time'] = time
    # df.loc[id]['miles'] = miles

pd.set_option("display.max_rows", None, "display.max_columns", None)
print(df)




#print(get_key())
#print(get_all_riders())
