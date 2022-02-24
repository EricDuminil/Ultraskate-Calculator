#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 10:11:14 2022

@author: ricou
"""
import requests
import requests_cache
import json
from datetime import timedelta
from pprint import pprint

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
    lap: int = 0
    miles: float = 0
    kilometers: float = 0

requests_cache.install_cache('dev_cache', expire_after=timedelta(days=1))

EVENT_ID = '192607'
RIDER_NAME = 'Mathieu'

BASE_URL = "https://my.raceresult.com/RRPublish/data"

def get_json_data(url):
    print(f"### Downloading {url}")
    r = requests.get(url)
    return json.loads(r.content)

def get_key(event_id=EVENT_ID):
    url = f"{BASE_URL}/config.php?eventid={event_id}&page=live&noVisitor=1"
    return get_json_data(url)['key']

def rider_dict(rider_id, position, _id, name, _team, laps, miles, time, diff):
    return {
            'id': int(rider_id),
            'name': name,
            'position': int(position.replace('.', '').replace('na','999')),
            'laps': int(laps),
            'time': time
        }

def get_all_riders(event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/list.php?eventid={event_id}&key={key}&listname=Result+Lists%7COverall+Results+-+Live&page=live&contest=0&r=leaders&l=100"
    table = get_json_data(url)['data']
    categories = [cat for team_or_not in table.values() for cat in team_or_not.values()]
    riders = [rider for riders in categories for rider in riders]
    return [rider_dict(*r) for r in riders if len(r) > 1]

def find_rider(name, event_id=EVENT_ID):
    riders = get_all_riders(event_id)
    return next(r for r in riders if name in r['name'])

def get_laps(rider, event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/list.php?eventid={event_id}&key={key}&listname=Online%7CLap+Details&page=live&contest=0&r=bib2&bib={rider['id']}"
    return get_json_data(url)['data']

def convert_to_racetec_format(rider):
    table = get_laps(rider)
    result = []
    for row in table:
        _id, lap, total_time, time = row
        result.append([f'Lap {lap}', total_time, time, rider['position'], rider['position']])
    return result


def get_participants(event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/list.php?eventid={event_id}&key={key}&listname=Participants%7CParticipants+List+123&page=participants&contest=0&r=all&l=0"
    return get_json_data(url)['data']

#rider = find_rider(RIDER_NAME)
#laps = get_laps(rider)
riders = []
for team_or_not, table in get_participants().items():
    for row in table:
        id, _id, _chip, name, team, clydesdale, age, discipline, division = row
        riders.append(Rider(int(id), name, team, clydesdale == 'Yes', age, discipline, division))
import pandas as pd
df = pd.DataFrame(riders)
df = df.set_index('id')
df = df.sort_index()
print(df)




#print(get_key())
#print(get_all_riders())
