import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import os
import streamlit as st
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import time
import altair as alt
from st_pages import Page, show_pages, add_page_title

# """
# Display of data is primarily conducted using Streamlit. Streamlit is an open-source Python library
# that enables users with minimal web development experience to create custom, intuitive and visually appealing 
# web applications. It is well-suited for machine learning and data science applications, providing a straightforward 
# way to display and interact with data.

# To read more: https://docs.streamlit.io/get-started

# ## MAIN FUNCTION:
#     -   Acts as the default page of the program with integration of all offshore sensors in mind
#     -   Provides a general overview of all relevant offshore sensor data for general offshore operations (e.g. chopper & vessel activities)
#     -   Separate scripts can be created to accommodate specific sensors (refer to directory structure)
#     -   Subsequent pages serves a specific function and displays more detailed information (refer to metocean department)

# Refer to Mainpage.py flowchart for visual explanation of code.

# To run file, on terminal enter:
# streamlit run {file_name}.py

# ## NOTE:
#     -   Script displays [-2] value of arrray for ALL instances to show latest values
#     -   ANGLE_DIFFERENCE represents the difference between True North & Platform values; NEEDS to be preconfigured in script for all 
#         related wind data (refer to metocean department for details)
#     -   Currently streamlit program is only locally hosted on device and CANNOT by accessed via internet. Only users on the same IP network
#         can view GUI display through local IP network.

# ## PROGRAM DIRECTORY STRUCTURE:
# /Main_folder
# ├── Mainpage.py
# └── Postprocess.py    
# └── full_code.py
# └── Pre-Processed data (Wind data ONLY)
# |   └── Raw data files
# └── Processed data V4 (Wind data ONLY)
# |   └── Processed data files
# └── Sensor pages
#     └── Windsensor1.py
#     └── Other Sensor page scripts

# ## TODO:
#     -   Integrate with reamaining other sensors & test offshore compatibility
#     -   Allow free access through dedicated domain through URL link 

# ## REFERENCES:
#     -   [Streamlit Official Documentation] https://pypi.org/project/st-pages/    
#     -   [Streamlit-Pages Library Documentation] https://pypi.org/project/st-pages/
 
# """

#True North - Platform north = ANGLE_DIFFERENCE 
# +ve difference = clockwise direction
# -ve difference = anticlockwise direction
ANGLE_DIFFERENCE = 180

def generate_filename(file_name):
    '''
    Getting the date and generate files based on date

    Returns : f{}
    '''
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    return f"{file_name}{today_date}.txt"

def check_datafile(file_path):
    """
    Checks if Pre-processed data file exists in directory. Application stops if no file is detected
    """    
    if not os.path.isfile(file_path):
        st.error("Data file not available. Ensure Pre-processed file is in the correct directory.")
        st.stop()

def create_folders(main_folder):
    """
    Creates folder based main_folder name and relative directory
    """    
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)

def get_data(path, max_retry = 20, delay = 10):
    """
    Handles common runtime errors by retrying attempts at returning processed data.

    Returns processed data from path directory
    """    
    attempt = 0
    while attempt < max_retry:
        try:
            data = pd.read_csv(path, sep = '\t')
            return data
        
        except FileNotFoundError:
            attempt += 1
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - File not found. Retrying (Attempt {attempt} of {max_retry})")
            time.sleep(delay)

        #Occurs at seemingly random intervals with no apparent reason. Retry attempts of 2-3 allows errors to pass
        except pd.errors.EmptyDataError:
            attempt += 1
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - No columns to parse from file. Retrying (Attempt {attempt} of {max_retry})")
            time.sleep(delay)

def calc_platnorth(degrees):
    """
    Calculates platform north values as per ANGLE_DIFFERENCE

    returns array of adjsuted_degrees
    """    
    global ANGLE_DIFFERENCE
    adjusted_degrees = (degrees + ANGLE_DIFFERENCE) % 360
    return adjusted_degrees

#For sensor display pages
show_pages(
    [
        Page("Mainpage.py", "Main Page - Overall View"),
        Page("Sensor pages/Windsensor1.py", "Wind Sensor"),
    ]
)

st.set_page_config(page_title="MetoMonitor Metstation", layout="wide")
try:
    print("Program Running")
    print("Program start: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    st.title("PETRONAS Metocean Station", anchor = False)
    update_placeholder = st.markdown("Last Updated: -") #Placeholders are used for display to prevent repetitive markdowns on application

    #Placeholders for data columns
    q1, q2, q3 = st.columns(3, gap = "medium")
    with q1:
        ################################ DISPLAY FOR WIND DATA ################################ 
        st.subheader("Wind Sensor", anchor = False, divider= "orange")
        p1, p2 = st.columns(2)
        display_1min_speed = p1.metric("1min - Wind Speed (m/s)", np.nan, "-", "off")
        display_1min_direction = p1.metric("1min - Wind Direction (°)", np.nan, "-", "off")
        display_1min_gust = p1.metric("1min - 3s Wind Gust (m/s)", np.nan, "-", "off")

        display_10min_speed = p2.metric("10min - Wind Speed (m/s)", np.nan, "-", "off")
        display_10min_direction = p2.metric("10min - Wind Direction (°)", np.nan, "-", "off")
        display_10min_gust = p2.metric("10min - 3s Wind Gust (m/s)", np.nan, "-", "off")
    
    with q2:
        ################################ DISPLAY FOR WAVE SENSORS ################################
        st.subheader("Wave Sensor", anchor = False, divider= "orange")
        b1, b2 = st.columns(2)
        display_sigwave = b1.metric("Sig. Wave Height", np.nan, "-", "off")
        display_tz = b1.metric("Tz" , np.nan, "-", "off")
        display_waterlvl = b1.metric("Water Level" , np.nan, "-", "off")

        display_maxwave = b2.metric("Max. Wave Height" , np.nan, "-", "off")
        display_tp = b2.metric("Tp" , np.nan, "-", "off")

    with q3:
        ################################ DISPLAY FOR CURRENT SENSORS ################################
        st.subheader("Current Sensor", anchor = False, divider= "orange")
        c1, c2 = st.columns(2)
        display_scurrentspd = c1.metric("Surface Current Speed", np.nan, "-", "off")
        display_watertemp = c1.metric("Water Temperature" , np.nan, "-", "off")
        display_currentdir = c2.metric("Surface Current Direction" , np.nan, "-", "off")
    
        
    #To choose true north or platform north - Default True North
    wind_not = st.selectbox(
        "Select Wind notation",
        ("True North", "Platform North"),
        index=0,
        label_visibility = "collapsed" 
    )

    ################################ DISPLAY FOR AMBIENT SENSORS ################################     
    st.header("Ambient Sensor Data", anchor = False, divider= "orange")
    #Need to add drop down menu to choose between INT, 1HR or Daily readings

    a1, a2, a3 = st.columns(3, gap = "small")
    display_pressure_qfe = a1.metric("B. Pressure (QFE)", np.nan, "-", "off")
    display_pressure_qnh = a1.metric("B. Pressure (QNH)" , np.nan, "-", "off")
    display_airtemp = a1.metric("Air Temperature" , np.nan, "-", "off")

    display_rhumidity = a2.metric("Relative Humidity" , np.nan, "-", "off")
    display_1min_visi = a2.metric("1-Minute Visibility" , np.nan, "-", "off")
    display_10min_visi = a2.metric("10-Minute Visibility" , np.nan, "-", "off")

    display_percipitation = a3.metric("Precipitation" , np.nan, "-", "off")
    display_cbase = a3.metric("Cloud Base" , np.nan, "-", "off")
    display_cstatus = a3.metric("Cloud Status" , np.nan, "-", "off")

    for i in range(3):
        st.markdown(" ")
    footer_html = """
    <div style='text-align: center;'>
    <p>Developed and designed by <a href='https://my.linkedin.com/in/faisal-hasbi-032b31248'>Faisal Hasbi</a>, with early contributions from <a href='https://www.linkedin.com/in/irfan-syafi/'>Irfan Syafi</a></p>
    </div>
    """
    footer_placeholder = st.empty()

    ################################ WIND DATA FILES ################################
    data_folder = "Processed data V4"
    mean_filename = "mean_data_"

    #Define subsequent data csv file names and directory for other sensors appropiately

    previous_date = datetime.date.today()

    ################################ Main loop ################################
    while True:
        footer_placeholder.markdown(footer_html, unsafe_allow_html=True)

        update_interval = False

        current_date = datetime.date.today()
        current_date_str = current_date.strftime("%Y-%m-%d")

        #Allows Postprocess.py to create processed data file
        if current_date != previous_date:
            time.sleep(20)
            previous_date = current_date
        
        #Opening mean file path - WIND
        mean_path = os.path.join(data_folder, generate_filename(mean_filename))

        #Define other sensor processed data file paths

        #Reading mean data
        mean_df = get_data(mean_path)
        mean_df['DateTime'] = pd.to_datetime(mean_df["DateTime"])

        #Reading mean data - OTHER SENSORS

        ################################ Display of data - WIND ################################
        if len(mean_df) > 2:

            #1min data
            windspeed_1min = mean_df["Wind Speed - m/s (1 min)"].iloc[-2]
            prev_ws_1min = mean_df["Wind Speed - m/s (1 min)"].iloc[-3]

            winddirection_1min = mean_df["Wind Direction - Deg (1 min)"].iloc[-2]
            prev_wd_1min = mean_df["Wind Direction - Deg (1 min)"].iloc[-3]

            gust_1min = mean_df["3-sec Gust - m/s (1 min)"].iloc[-2]
            prev_gs_1min = mean_df["3-sec Gust - m/s (1 min)"].iloc[-3]

            #To calculate platform north wind direction values
            mean_df["Wind Direction - Deg (1 min) Platform North"] = mean_df["Wind Direction - Deg (1 min)"].apply(calc_platnorth)
            winddirection_1min_platnorth = mean_df["Wind Direction - Deg (1 min) Platform North"].iloc[-2]
            prev_wd_1min_platnorth = mean_df["Wind Direction - Deg (1 min) Platform North"].iloc[-3]

            #handling for NaN values - 1min
            windspeed_1min = pd.to_numeric(windspeed_1min, errors = "coerce")
            prev_ws_1min = pd.to_numeric(prev_ws_1min, errors = "coerce")
            winddirection_1min = pd.to_numeric(winddirection_1min, errors = "coerce")
            prev_wd_1min = pd.to_numeric(prev_wd_1min, errors = "coerce")
            gust_1min = pd.to_numeric(gust_1min, errors = "coerce")
            prev_gs_1min = pd.to_numeric(prev_gs_1min, errors = "coerce")
            winddirection_1min_platnorth = pd.to_numeric(winddirection_1min_platnorth, errors = "coerce")
            prev_wd_1min_platnorth = pd.to_numeric(prev_wd_1min_platnorth, errors = "coerce")

            if pd.notna(windspeed_1min) and pd.notna(prev_ws_1min):
                delta_windspd_1min = (windspeed_1min - prev_ws_1min).round(4)
            else:
                delta_windspd_1min = np.nan
            
            if pd.notna(winddirection_1min) and pd.notna(prev_wd_1min):
                delta_winddir_1min = winddirection_1min - prev_wd_1min
            else:
                delta_winddir_1min = np.nan
            
            if pd.notna(gust_1min) and pd.notna(prev_gs_1min):
                delta_gust_1min = (gust_1min - prev_gs_1min).round(4)
            else:
                delta_gust_1min = np.nan

            if pd.notna(winddirection_1min_platnorth) and pd.notna(prev_wd_1min_platnorth):
                delta_winddir_1min_platnorth = (winddirection_1min_platnorth - prev_wd_1min_platnorth).round(4)
            else:
                delta_winddir_1min_platnorth = np.nan    

            #10min data display
            windspeed_10min = mean_df["Wind Speed - m/s (10 min)"].iloc[-2]
            prev_ws_10min = mean_df["Wind Speed - m/s (10 min)"].iloc[-3]

            winddirection_10min = mean_df["Wind Direction - Deg (10 min)"].iloc[-2]
            prev_wd_10min = mean_df["Wind Direction - Deg (10 min)"].iloc[-3]

            gust_10min = mean_df["3-sec Gust - m/s (10 min)"].iloc[-2]
            prev_gs_10min= mean_df["3-sec Gust - m/s (10 min)"].iloc[-3]

            #To handle platform north
            mean_df["Wind Direction - Deg (10 min) Platform North"] = mean_df["Wind Direction - Deg (10 min)"].apply(calc_platnorth)
            winddirection_10min_platnorth = mean_df["Wind Direction - Deg (10 min) Platform North"].iloc[-2]
            prev_wd_10min_platnorth = mean_df["Wind Direction - Deg (10 min) Platform North"].iloc[-3]

            #handling for NaN values - 10mins
            windspeed_10min = pd.to_numeric(windspeed_10min, errors = "coerce")
            prev_ws_10min = pd.to_numeric(prev_ws_10min, errors = "coerce")
            winddirection_10min = pd.to_numeric(winddirection_10min, errors = "coerce")
            prev_wd_10min = pd.to_numeric(prev_wd_10min, errors = "coerce")
            gust_10min = pd.to_numeric(gust_10min, errors = "coerce")
            prev_gs_10min = pd.to_numeric(prev_gs_10min, errors = "coerce")
            winddirection_10min_platnorth = pd.to_numeric(winddirection_10min_platnorth, errors = "coerce")
            prev_wd_10min_platnorth = pd.to_numeric(prev_wd_10min_platnorth, errors = "coerce")

            if pd.notna(windspeed_10min) and pd.notna(prev_ws_10min):
                delta_windspd_10min = (windspeed_10min - prev_ws_10min).round(4)
            else:
                delta_windspd_10min = np.nan
            
            if pd.notna(winddirection_10min) and pd.notna(prev_wd_10min):
                delta_winddir_10min = winddirection_10min - prev_wd_10min
            else:
                delta_winddir_10min = np.nan
            
            if pd.notna(gust_10min) and pd.notna(prev_gs_10min):
                delta_gust_10min = (gust_10min - prev_gs_10min).round(4)
            else:
                delta_gust_10min = np.nan

            if pd.notna(winddirection_10min_platnorth) and pd.notna(prev_wd_10min_platnorth):
                delta_winddir_10min_platnorth = (winddirection_10min_platnorth - prev_wd_10min_platnorth).round(4)
            else:
                delta_winddir_1min_platnorth = np.nan 

            update_interval = True
    
        else:
            windspeed_1min = np.nan
            delta_windspd_1min = np.nan
            winddirection_1min = np.nan
            delta_winddir_1min = np.nan
            gust_1min = np.nan
            delta_gust_1min = np.nan
            winddirection_1min_platnorth = np.nan
            prev_wd_1min_platnorth = np.nan

            windspeed_10min = np.nan
            delta_windspd_10min = np.nan
            winddirection_10min = np.nan
            delta_winddir_10min = np.nan
            gust_10min = np.nan
            delta_gust_10min = np.nan
            winddirection_10min_platnorth = np.nan
            prev_wd_10min_platnorth = np.nan

        #To update display - WIND
        display_1min_speed.metric("1min - Wind Speed (m/s)", windspeed_1min, f"{delta_windspd_1min} (m/s)", "off")
        display_1min_gust.metric("1min - 3s Wind Gust (m/s)", gust_1min, f"{delta_gust_1min} (m/s)", "off")
        display_10min_speed.metric("10min - Wind Speed (m/s)", windspeed_10min, f"{delta_windspd_10min} (m/s)", "off")
        display_10min_gust.metric("10min - 3s Wind Gust (m/s)", gust_10min, f"{delta_gust_10min} (m/s)", "off")

        if wind_not == "True North":
            display_1min_direction.metric("1min - Wind Direction (°)", winddirection_1min, f"{delta_winddir_1min} (°)", "off")
            display_10min_direction.metric("10min - Wind Direction (°)", winddirection_10min, f"{delta_winddir_10min} (°)", "off")
        
        elif wind_not == "Platform North":
            display_1min_direction.metric("1min - Wind Direction (°)", winddirection_1min_platnorth, f"{delta_winddir_1min_platnorth} (°)", "off")
            display_10min_direction.metric("10min - Wind Direction (°)", winddirection_10min_platnorth, f"{delta_winddir_10min_platnorth} (°)", "off")         
        

        #To update time 
        if update_interval == True:
            update_min = datetime.datetime.now().strftime("%H:%M:00")
            update_placeholder.markdown(f"Last Updated: {update_min}")

        time.sleep(15) 

except:
    print("Program ended....")
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Program end: " + end_time)
