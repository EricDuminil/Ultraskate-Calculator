from flask import Flask, render_template
import json
from datetime import timedelta
from pprint import pprint
from math import ceil

RIDER_NAME = 'Mathieu_Bon'

# Miami previous mileages
mileage_2018 = 289.6
mileage_2019 = 262.8
mileage_2020 = 226.3

# Track length in miles
lap_distance = 3.15 / 1.609

total_ultra_time_sec = 24 * 60 * 60

################ From CSV ##################

def get_data_from_csv(rider):
    with open(f"/home/ricou/www/ultra_graph/data/dutch_ultra_2022/{rider.lower()}.csv") as f:
        table = []
        for line in f:
            time, distance = [float(x) for x in line.split()]
            lap = int(round(distance / lap_distance))
            position = '?'
            row = (lap, time, distance, position, position)
            if (not table) or table[-1][0] != row[0]:
                table.append(row)
        return table

#################################################
# Calculating the data

def ultra_calc(input_list):
    lap_list = []
    lap_count = 0
    elapsed_time_list = []
    # for single_lap in input_list:

        # hours, minutes, seconds = single_lap[2].split(':')

        # position = single_lap[4]

        # laptime_second = round(float(seconds)) + (int(minutes) * 60) + (int(hours) * 3600)

        # speed = (lap_distance / 0.62137119) / laptime_second * 3600

        # lap_count += 1

        # current_mileage = lap_count * lap_distance

        # lap_data = f"Lap {lap_count} in {speed:.2f} km/h / {current_mileage:.2f} miles"

        # lap_list.append(lap_data)
        # elapsed_time_list.append(laptime_second)

    start_lap, start_time, _, _, _ = input_list[0]
    end_lap, end_time, _, _, _ = input_list[-1]
    lap_count = end_lap - start_lap
    time = (end_time - start_time) * 3600
    return lap_count * lap_distance, lap_count, '?', time, []


def miles_to_km(miles):
    return miles * 1.609344


def average_speed(total_miles_input, total_elapsed_time_input):
    mile_second = (total_miles_input / total_elapsed_time_input)
    average_speed_km = miles_to_km(mile_second) * 60 * 60
    return average_speed_km, mile_second


def average_speed_to_goal(mileage_goal, total_km, remaining_time):
    required_distance = ceil(mileage_goal / lap_distance) * lap_distance
    speed = ((miles_to_km(required_distance) - total_km) / remaining_time) * 3600
    return speed


def remaining_lap_calc(mileage_goal, lap_count):
    total_laps = ceil(mileage_goal / lap_distance)
    return total_laps - lap_count


def calculate_output_list():
    race_data_final = get_data_from_csv(RIDER_NAME)

    total_miles, lap_count, position, total_elapsed_time, lap_list = ultra_calc(race_data_final)
    results_last5 = ultra_calc(race_data_final[-6:])
    results_last = ultra_calc(race_data_final[-2:])

    remaining_time = total_ultra_time_sec - total_elapsed_time

    total_km = miles_to_km(total_miles)

    print(f"{total_miles:.2f} miles.")

    total_miles_last5 = results_last5[0]
    total_elapsed_time_last5 = results_last5[3]

    total_miles_last = results_last[0]
    total_elapsed_time_last = results_last[3]

    average_speed_total = average_speed(total_miles, total_elapsed_time)
    average_speed_last5 = average_speed(total_miles_last5, total_elapsed_time_last5)
    average_speed_last = average_speed(total_miles_last, total_elapsed_time_last)

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
            f"{remaining_lap_calc(mileage_2020, lap_count)} laps",
            f"Average to 250 miles : {average_speed_to_goal(250, total_km, remaining_time):.2f} km/h / "
            f"{remaining_lap_calc(250, lap_count)} laps",
            f"Average to {mileage_2019:.1f} miles : {average_speed_to_goal(mileage_2019, total_km, remaining_time):.2f} km/h / "
            f"{remaining_lap_calc(mileage_2019, lap_count)} laps",
            f"Average to {mileage_2018:.1f} miles : {average_speed_to_goal(mileage_2018, total_km, remaining_time):.2f} km/h / "
            f"{remaining_lap_calc(mileage_2018, lap_count)} laps",
            f"Average to 300 miles : {average_speed_to_goal(300, total_km, remaining_time):.2f} km/h / "
            f"{remaining_lap_calc(300, lap_count)} laps"
            ], lap_list

app = Flask(__name__)

@app.route("/")
def index():
    try:
        output_list, lap_list = calculate_output_list()
        return render_template("index.html",
                               output_list=output_list,
                               lap_list=lap_list[::-1])
    except StopIteration:
        return "Live data not yet available."


if __name__ == "__main__":
    app.run(host="0.0.0.0")
