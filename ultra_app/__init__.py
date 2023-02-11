from flask import Flask, render_template
import requests
import requests_cache
import json
from datetime import timedelta

requests_cache.install_cache('prod_cache',
                             expire_after=60,  # [s]
                             cache_control=True,
                             stale_if_error=False,
                             use_temp=True)

EVENT_ID = '204047'  # For Miami 2023
#EVENT_ID = '192607'
EVENT_NAME = 'Miami Ultraskate 2023'
RIDER_NAME = 'Mathieu'
BASE_URL = "https://my.raceresult.com"

# Miami previous mileages
mileage_2018 = 289.7
mileage_2019 = 262.8
mileage_2020 = 226.3

# Track length in miles
lap_distance = 1.46

total_ultra_time_sec = 24 * 60 * 60

################ RaceResults ##################


def get_json_data(url):
    print(f"### Downloading {url}")
    r = requests.get(url)
    return json.loads(r.content)


def get_key(event_id=EVENT_ID):
    url = f"{BASE_URL}/{event_id}/RRPublish/data/config?page=participants&noVisitor=1"
    return get_json_data(url)['key']


def rider_dict(rider_id, position, _id, name, _team, laps, miles, time, diff):
    return {
        'id': int(rider_id),
        'name': name,
        'position': int(position.replace('.', '').replace('na', '999')),
        'laps': int(laps),
        'time': time
    }


def get_all_riders(event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/{event_id}/RRPublish/data/list?key={key}&listname=Result%20Lists%7COverall%20Results%20-%20Live&page=live&contest=0&r=leaders&l=100"
    table = get_json_data(url)['data']
    categories = [cat for team_or_not in table.values()
                  for cat in team_or_not.values()]
    riders = [rider for riders in categories for rider in riders]
    return [rider_dict(*r) for r in riders if len(r) > 1]


def find_rider(name, event_id=EVENT_ID):
    riders = get_all_riders(event_id)
    return next(r for r in riders if name in r['name'])


def get_laps(rider, event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/{event_id}/RRPublish/data/list?key={key}&listname=Online%7CLap%20Details&page=live&contest=0&r=bib2&bib={rider['id']}"
    return get_json_data(url)['data']


def fill_hours(time):
    if time.count(':') == 1:
        return '0:' + time
    else:
        return time


def convert_to_racetec_format(rider):
    table = get_laps(rider)
    result = []
    for row in table:
        _id, lap, total_time, time = row
        result.append([f'Lap {lap}',
                       fill_hours(total_time),
                       fill_hours(time),
                       rider['position'],
                       rider['position']])
    return result

#################################################
# Calculating the data


def ultra_calc(input_list):
    lap_list = []
    lap_count = 0
    elapsed_time_list = []
    for single_lap in input_list:

        hours, minutes, seconds = single_lap[2].split(':')

        position = single_lap[4]

        laptime_second = round(float(seconds)) + \
            (int(minutes) * 60) + (int(hours) * 3600)

        speed = (lap_distance / 0.62137119) / laptime_second * 3600

        lap_count += 1

        current_mileage = lap_count * lap_distance

        lap_data = f"Lap {lap_count} in {speed:.2f} km/h / {current_mileage:.2f} miles"

        lap_list.append(lap_data)
        elapsed_time_list.append(laptime_second)

    return current_mileage, lap_count, position, sum(elapsed_time_list), lap_list


def miles_to_km(miles):
    return miles * 1.609344


def average_speed(total_miles_input, total_elapsed_time_input):
    mile_second = (total_miles_input / total_elapsed_time_input)
    average_speed_km = miles_to_km(mile_second) * 60 * 60
    return average_speed_km, mile_second


def average_speed_to_goal(mileage_goal, total_km, remaining_time):
    speed = ((miles_to_km(mileage_goal) - total_km) / remaining_time) * 3600
    return speed


def remaining_lap_calc(input_remaining, lap_count):
    return input_remaining - lap_count


def calculate_output_list():
    rider = find_rider(RIDER_NAME)
    race_data_final = convert_to_racetec_format(rider)

    total_miles, lap_count, position, total_elapsed_time, lap_list = ultra_calc(
        race_data_final)
    results_last5 = ultra_calc(race_data_final[-5:])
    results_last = ultra_calc(race_data_final[-1:])

    remaining_time = total_ultra_time_sec - total_elapsed_time

    total_km = miles_to_km(total_miles)

    print(f"{total_miles:.2f} miles.")

    total_miles_last5 = results_last5[0]
    total_elapsed_time_last5 = results_last5[3]

    total_miles_last = results_last[0]
    total_elapsed_time_last = results_last[3]

    average_speed_total = average_speed(total_miles, total_elapsed_time)
    average_speed_last5 = average_speed(
        total_miles_last5, total_elapsed_time_last5)
    average_speed_last = average_speed(
        total_miles_last, total_elapsed_time_last)

    mile_per_second = average_speed_total[1]
    mile_projection = remaining_time * mile_per_second + total_miles

    return [
        f"Position : {position} / Laps : {lap_count}",
        f"Elapsed : {timedelta(seconds=total_elapsed_time)} / Remaning : {timedelta(seconds=remaining_time)}",
        f"Mileage : {total_miles:.2f} miles / {total_km:.2f} km",
        f"Average speed : {average_speed_total[0]:.2f} km/h",
        f"Projection at current speed : {mile_projection:.2f} miles",
        f"Average on last lap: {average_speed_last[0]:.2f} km/h",
        f"Average on last 5 laps: {average_speed_last5[0]:.2f} km/h",
        f"Average to {mileage_2020:.1f} miles : {average_speed_to_goal(mileage_2020, total_km, remaining_time):.2f} km/h / "
        f"{remaining_lap_calc(155, lap_count)} laps",
        f"Average to 250 miles : {average_speed_to_goal(251.12, total_km, remaining_time):.2f} km/h / "
        f"{remaining_lap_calc(172, lap_count)} laps",
        f"Average to {mileage_2019:.1f} miles : {average_speed_to_goal(mileage_2019, total_km, remaining_time):.2f} km/h / "
        f"{remaining_lap_calc(180, lap_count)} laps",
        f"Average to {mileage_2018:.1f} miles : {average_speed_to_goal(mileage_2018, total_km, remaining_time):.2f} km/h / "
        f"{remaining_lap_calc(199, lap_count)} laps",
        f"Average to 300 miles : {average_speed_to_goal(300, total_km, remaining_time):.2f} km/h / "
        f"{remaining_lap_calc(206, lap_count)} laps"
    ], lap_list


app = Flask(__name__)


@app.route("/")
def index():
    try:
        output_list, lap_list = calculate_output_list()
        return render_template("index.html",
                               output_list=output_list,
                               lap_list=lap_list[::-1],
                               event_name=EVENT_NAME,
                               rider_name=RIDER_NAME
                               )
    except StopIteration:
        return "Live data not yet available."


def get_all_riders_and_categories(event_id=EVENT_ID):
    key = get_key(event_id)
    url = f"{BASE_URL}/{event_id}/RRPublish/data/list?key={key}&listname=Participants%7CIndividual%20Skaters&page=participants&contest=0&r=all&l=0"
    table = get_json_data(url)['data']
    return [x for row in table.values() for x in row]


@app.route("/categories")
def categories():
    data = get_all_riders_and_categories()
    riders = get_all_riders()
    import pandas as pd
    df2 = pd.DataFrame(riders)
    df = pd.DataFrame(data, columns=['id', 'bib2', 'x', 'name', 'team_name',
                      'age', 'discipline', 'gender', 'clydesdale', 'nation'])

    df = df[['id', 'name', 'age', 'discipline', 'gender', 'clydesdale', 'nation']]
    df['id'] = df['id'].astype(int)
    df2 = df2.drop(columns=['name'])
    df2.position = df2['position'].astype("Int16")
    df2.laps = df2['laps'].astype("Int16")
    df2['miles'] = df2.laps * 1.46
    df.clydesdale = df.clydesdale == 'Yes'
    df3 = df.merge(df2, on='id', how='left')
    df3 = df3.set_index('id')
    df3 = df3.sort_values(['position', 'laps'], ascending=[True, False])
    df3.nation = df3.nation.str.replace('\[img:flags\/', '').str.replace('.gif]', '')
    return df3.to_html()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
