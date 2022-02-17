import requests
from bs4 import BeautifulSoup
from datetime import timedelta
from flask import Flask, render_template

# Miami previous mileages
mileage_2019 = 262.8
mileage_2020 = 226.3

# Track length in miles
lap_distance = 1.46


# Webpages to scrape
mia_mathieu_2020 = "http://jms.racetecresults.com/myresults.aspx?uid=16370-400-1-423957"
mia_mathieu_2019 = "http://jms.racetecresults.com/myresults.aspx?CId=16370&RId=352&EId=1&AId=141108"


# Scraping the entire webpage date and assigning it to 'soup'

website = requests.get(mia_mathieu_2019)
soup = BeautifulSoup(website.content, 'html.parser')

time_id = soup.find_all(class_='ltw-cell-padless ltw-cell-center')
lap = soup.find_all(class_='ltw-cell-padless ltw-cell-left')


# Variable entire_soup contains all the rows data

entire_soup = soup.find_all("td", class_="ltw-cell-padless")

temp_list = []
race_data = []
race_data_final = []


x = 0

for one in entire_soup:

    if x < 5:
        # Each row having 5 columns, temp_list is copied to race_data until the 5th entry
        temp_list.append(one.text)
        x = x + 1

    else:
        race_data.append(temp_list)
        temp_list = []
        temp_list.append(one.text)
        x = 1


for one in race_data:
    if one[1] != "":
        race_data_final.append(one)


# Calculating the data

def ultra_calc(input_list):
    lap_list = []
    lap_count = 0
    elapsed_time_list = []
    for single_lap in input_list:

        hours, minutes, seconds = single_lap[2].split(':')

        position = single_lap[4]

        laptime_second = int(seconds) + (int(minutes) * 60) + (int(hours) * 3600)

        speed = (lap_distance / 0.62137119) / laptime_second * 3600

        lap_count += 1

        current_mileage = lap_count * lap_distance

        lap_data = f"Lap {lap_count} in {speed:.2f} km/h / {current_mileage:.2f} miles"
        print(single_lap)
        print(lap_data)

        lap_list.append(lap_data)
        elapsed_time_list.append(laptime_second)

    return current_mileage, lap_count, position, sum(elapsed_time_list), lap_list


total_ultra_time_sec = 24 * 60 * 60

results = ultra_calc(race_data_final)

results_last5 = ultra_calc(race_data_final[-5:])

results_last = ultra_calc(race_data_final[-1:])


def miles_to_km(miles):
    return miles * 1.609344


def average_speed(total_miles_input, total_elapsed_time_input):

    mile_second = (total_miles_input / total_elapsed_time_input)
    average_speed_km = miles_to_km(mile_second) * 60 * 60
    return average_speed_km, mile_second


def average_speed_to_goal(mileage_goal):
    speed = ((miles_to_km(mileage_goal) - total_km) / remaining_time) * 3600
    return speed


def remaining_lap_calc(input_remaining):
    return input_remaining - results[1]


total_elapsed_time = results[3]
remaining_time = total_ultra_time_sec - total_elapsed_time

total_miles = results[0]
total_km = miles_to_km(total_miles)

total_miles_last5 = results_last5[0]
total_elapsed_time_last5 = results_last5[3]

total_miles_last = results_last[0]
total_elapsed_time_last = results_last[3]

average_speed_total = average_speed(total_miles, total_elapsed_time)
average_speed_last5 = average_speed(total_miles_last5, total_elapsed_time_last5)
average_speed_last = average_speed(total_miles_last, total_elapsed_time_last)

mile_per_second = average_speed_total[1]
mile_projection = remaining_time * mile_per_second + total_miles


def calculate_output_list():
    return [
            f"Position : {results[2]} / Laps : {results[1]}",
            f"Elapsed : {timedelta(seconds=total_elapsed_time)} / Remaning : {timedelta(seconds=remaining_time)}",
            f"Mileage : {total_miles:.2f} miles / {total_km:.2f} km",
            f"Average speed : {average_speed_total[0]:.2f} km/h",
            f"Projection at current speed : {mile_projection:.2f} miles",
            f"Average on last lap: {average_speed_last[0]:.2f} km/h",
            f"Average on last 5 laps: {average_speed_last5[0]:.2f} km/h",
            f"Average to {mileage_2020:.1f} miles : {average_speed_to_goal(mileage_2020):.2f} km/h / "
            f"{remaining_lap_calc(155)} laps",
            f"Average to 250 miles : {average_speed_to_goal(251.12):.2f} km/h / "
            f"{remaining_lap_calc(172)} laps",
            f"Average to {mileage_2019:.1f} miles : {average_speed_to_goal(mileage_2019):.2f} km/h / "
            f"{remaining_lap_calc(180)} laps",
            f"Average to 300 miles : {average_speed_to_goal(300):.2f} km/h / "
            f"{remaining_lap_calc(206)} laps"
            ]

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", output_list=calculate_output_list(), lap_list=results[4])


if __name__ == "__main__":
    app.run(host="0.0.0.0")
