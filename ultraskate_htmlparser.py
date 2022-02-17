import requests
from bs4 import BeautifulSoup
from datetime import timedelta
from flask import Flask, render_template

# Miami previous mileages
mileage_2019 = 262.8
mileage_2020 = 226.3

# Track length in miles
lap_distance = 1.46

total_ultra_time_sec = 24 * 60 * 60

# Webpages to scrape
mia_mathieu_2020 = "http://jms.racetecresults.com/myresults.aspx?uid=16370-400-1-423957"
mia_mathieu_2019 = "http://jms.racetecresults.com/myresults.aspx?CId=16370&RId=352&EId=1&AId=141108"


def download_data(url=mia_mathieu_2019):
    # Scraping the entire webpage date and assigning it to 'soup'

    website = requests.get(mia_mathieu_2019)
    soup = BeautifulSoup(website.content, 'html.parser')

    # Needed?
    #lap = soup.find_all(class_='ltw-cell-padless ltw-cell-left')


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

    return race_data_final



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
    race_data_final = download_data()

    total_miles, lap_count, position, total_elapsed_time, lap_list = ultra_calc(race_data_final)
    results_last5 = ultra_calc(race_data_final[-5:])
    results_last = ultra_calc(race_data_final[-1:])

    remaining_time = total_ultra_time_sec - total_elapsed_time

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
            f"Average to 300 miles : {average_speed_to_goal(300, total_km, remaining_time):.2f} km/h / "
            f"{remaining_lap_calc(206, lap_count)} laps"
            ], lap_list

app = Flask(__name__)

@app.route("/")
def index():
    output_list, lap_list = calculate_output_list()
    return render_template("index.html",
                           output_list=output_list,
                           lap_list=lap_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
