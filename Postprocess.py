import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import os, sys
import time

"""
Primary script for handling post processing of raw data from sensor. Script operates in
tandem with full_code.py to continously output processed data csv files.

## MAIN SCRIPT FUNCTION:
    -   Generates processed data CSV files sorted by date as output (Aggregated time series data resampled in 1 min intervals)
    -   Able to continously produce output nonstop as long as raw data is received
    -   Utilizes rolling average techniques* to achieve continous update of processed data in 1 minute intervals
    -   Utilizes Vector averaging* to calculate average wind direction
    -   Calculates 3-sec gust and its subsequent averages

## NOTE:
    -   Processed data CSV format is based on metocean requirements/standards. Refer back to metocean department

## BRIEF EXPLANATION OF ROLLING AVERAGE ALGORITHM
    -   A rolling/moving average is a common method used to calculate trends over different time intervals
    -   Achieved by averaging data points over a specified window that moves through the data 
        •   For raw data collected over frequency of 1 Hz: 10 min = 600 data, 1 hour = 3600 data

## REFERENCES:
    -   [Pandas rolling documentation] https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html
    -   [How to calculate MOVING AVERAGE in a Pandas DataFrame?] https://www.geeksforgeeks.org/how-to-calculate-moving-average-in-a-pandas-dataframe/
    -   [Vector vs. Scalar Averaging of Wind Data] https://www.sodar.com/FYI/vector_vs_scalar.html
    -   [Direction Conventions and Conversions] https://www.xmswiki.com/wiki/Direction_Conventions_and_Conversions
"""

def generate_filename(file_name):
    """
    Returns file_name as string that contains file name and current date
    """

    today_date = datetime.date.today().strftime("%Y-%m-%d")
    return f"{file_name}{today_date}.txt"

def check_datafile(file_path):
    """
    Checks if data file exists as given file path. System exits if file not found.
    """

    if not os.path.isfile(file_path):
        sys.exit("Data file not available. Ensure Pre-processed file is in the correct directory.")

def create_folders(main_folder):
    """
    Creates folder based main_folder name and relative directory
    """
    
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)

def calc_degrees(u, v):
    """
    Calculates value of angle (degrees) based on U and V components. Angles is based on NAUTICAL convention*
    Returns array of angles
    """

    condition = (u==0) & (v==0)
    angles = (np.degrees(np.arctan2(-v, -u)) % 360).round(0)
    angles[condition] = np.nan
    return angles

def roll_avg(df,window):
    """
    10 mins - window = 600

    1 hour - window = 3600

    Returns resampled rolled average of given df with specified window
    """

    average = df.rolling(window = window).mean()
    average = average.resample("1min").mean().round(4)
    return average

def roll_gust(df, window):
    """
    10 mins - window = 600

    1 hour - window = 3600

    Returns resampled rolled 3-sec gust of given df with specified window
    """

    rolled_gust = df.rolling(window = window).max()
    rolled_gust = rolled_gust.resample("1min").max()
    return rolled_gust

####################### Program Start #######################
try:
    print("Program Running")
    program_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Program start: " + program_start)

    data_folder = "Processed data V4"
    create_folders(data_folder)

    previous_date = datetime.date.today()

    while True:
        current_date = datetime.date.today()
        current_date_str = current_date.strftime("%Y-%m-%d")

        if current_date != previous_date:
            time.sleep(5)
            previous_date = current_date

        raw_directory = "Pre-Processed data"
        raw_file = f"raw_wind_data_{current_date_str}.txt"
        raw_path = os.path.join(raw_directory, raw_file)
        check_datafile(raw_path)

        #Creating mean file path
        mean_directory = f"{data_folder}"
        mean_filename = "mean_data_"
        mean_path = os.path.join(data_folder, generate_filename(mean_filename))

        #Reading raw data
        df = pd.read_csv(raw_path, sep = '\t')
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df = df.set_index('DateTime')

        #Calculating 3 second gust based on raw data file 
        df["3 second gust"] = df["WindSpeed (m/s)"].rolling(window = 3).mean().round(4)
        df["3 second gust"].fillna(np.nan)

        #1 min data
        ws_mean_1min = df["WindSpeed (m/s)"].resample('1min').mean().round(4)
        u_mean_1min = df["U"].resample('1min').mean().round(4)
        v_mean_1min = df["V"].resample("1min").mean().round(4)
        deg_result_1min = calc_degrees(u_mean_1min, v_mean_1min)
        deg_result_1min = deg_result_1min.fillna(np.nan)
        gst_1min = df["3 second gust"].resample("1min").max()

        #rolled average of 10min and 1 hour data
        ws_mean_10min = roll_avg(df["WindSpeed (m/s)"],window=600)
        u_mean_10min = roll_avg(df["U"], window=600)
        v_mean_10min = roll_avg(df["V"], window=600)
        deg_result_10min = calc_degrees(u_mean_10min, v_mean_10min) #Vector averaging
        deg_result_10min = deg_result_10min.fillna(np.nan)
        gst_10min = roll_gust(df['3 second gust'], window=600)

        ws_mean_1hour = roll_avg(df["WindSpeed (m/s)"], window=3600)
        u_mean_1hour = roll_avg(df["U"], window=3600)
        v_mean_1hour = roll_avg(df["V"], window=3600)
        deg_result_1hour = calc_degrees(u_mean_1hour, v_mean_1hour) #Vector averaging
        deg_result_1hour = deg_result_1hour.fillna(np.nan)
        gst_1hour = roll_gust(df['3 second gust'], window=600)

        #Saving to CSV file
        mean_df = pd.concat([ws_mean_1min, deg_result_1min, gst_1min, ws_mean_10min, deg_result_10min, gst_10min, ws_mean_1hour, deg_result_1hour, gst_1hour], axis = 1)
        mean_df.columns = [
            "Wind Speed - m/s (1 min)",
            "Wind Direction - Deg (1 min)",
            "3-sec Gust - m/s (1 min)",
            "Wind Speed - m/s (10 min)",
            "Wind Direction - Deg (10 min)",
            "3-sec Gust - m/s (10 min)",
            "Wind Speed - m/s (1 hour)",
            "Wind Direction - Deg(1 hour)",
            "3-sec Gust - m/s (1 hour)"
        ]
        mean_df = mean_df[mean_df.index.date == current_date]
        mean_df.reset_index(inplace=True)
        mean_df.to_csv(mean_path, sep = '\t',  mode = 'w', na_rep = np.nan)

        time.sleep(15)

except KeyboardInterrupt:
    print("Program ended....")
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Program end: " + end_time)