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
import zipfile
import io

# """
# Separate scripts are necessary to compute and display sensor-specific information. Like Mainpage.py Streamlit is used to
# represent displayed data. Script pages only run when their respective pages are opened. This approach prevents unnecessary 
# resource consumption. Save script pages as per program directory structure.

# Page scripts can be coded to fit whatever specific needs are required by metocean department. 

# ## NOTE:
#     -   Script displays [-2] value of arrray for ALL instances to show latest values
#     -   ANGLE_DIFFERENCE represents the difference between True North & Platform values; NEEDS to be preconfigured in script for all 
#         related wind data (refer to metocean department for details)
#     -   Currently streamlit program is only locally hosted on device and CANNOT by accessed via internet. Only users on the same IP network
#         can view GUI display through local IP network.

# ## TODO:
#     -   Improve file saving feature by enabling bulk-save of files by month

# """

#True North - Platform north 
# +ve difference = clockwise direction
# -ve difference = anticlockwise direction
ANGLE_DIFFERENCE = 180

def generate_filename(file_name):
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

def wind_plot(wd = [], ws = [], mode = ''):
    """
    Creates wind plots using windrose library. Function saves windplot graph as .jpg image to be displayed in Streamlit application.

    Parameters:
    -   wd: Array for wind direction (DEGREES)
    -   ws: Array for wind speed (m/s)
    -   mode (str): Name for saved .jpg file
    
        •   "empty": For cases when empty windplot is needed and saves windplot as empty.jpg (NOTE: wd & ws can be left empty)

        •   "1min": Used in Windsensor.py wind dial. Creates windplot with no legend as 1min.jpg 
        
        •   "1hour", "1day", "7days", "30days": All used for Historical data representation and saved as given mode.jpg   

    windrose Documentation: https://windrose.readthedocs.io/en/latest/
    """

    fig_bg_color = 'white'
    ax_bg_color = "white"

    if mode == "empty":
        fig = plt.figure(figsize=(6,6), facecolor=fig_bg_color)  
        ax = WindroseAxes.from_ax(fig = fig)
        ax.set_facecolor(ax_bg_color)
        ax.set_legend()

        # Set the directional notations to white
        for label in ax.get_xticklabels():
            label.set_color('black')

        plt.savefig(f"{mode}.jpg", facecolor=fig_bg_color, transparent = False)
        plt.close()
    
    else:
        fig = plt.figure(figsize=(6,6), facecolor=fig_bg_color)   
        ax = WindroseAxes.from_ax(fig = fig)
        ax.set_facecolor(ax_bg_color)

        if mode == "1min":
            ax.bar(wd, ws, normed=True, opening=0.8, edgecolor="white")

        else:
            ax.bar(wd, ws, normed=True, opening=0.8, edgecolor="white")
            leg = ax.set_legend()
            plt.setp(leg.get_texts(), color='black')

        for label in ax.get_xticklabels():
            label.set_color('black')
            
        fig.patch.set_facecolor(fig_bg_color)
        plt.savefig(f"{mode}.jpg", facecolor=fig_bg_color, transparent = False)
        plt.close()

def ws_time(data, mode = ''):
    """
    data: Dataframe containing DateTime and Windspeed
    mode (str): specifies Y-axis title of graph

    e.g. data
    data = pd.DataFrame({
        "DateTime": datetime_values,
        "Wind Speed": ws_values
    })

    Returns alt.Chart object to be dispalyed by Streamlit
    
    To read more: https://docs.streamlit.io/develop/api-reference/charts/st.altair_chart
    """
    
    if mode:
        line_chart = alt.Chart(data).mark_line(color='orange').encode(
            x=alt.X('DateTime:T', axis=alt.Axis(title=f"DateTime ({mode})", labelColor='black', titleColor='black')),
            y=alt.Y('Wind Speed:Q', axis=alt.Axis(title='Wind Speed (m/s)', labelColor='black', titleColor='black'))
        ).properties(
            background='white'
        ).configure_axis(
            labelColor='black',
            titleColor='black'
        )
    
    else: #mode not specified for Past 1 hour graph
        line_chart = alt.Chart(data).mark_line(color='orange').encode(
            x=alt.X('DateTime:T', axis=alt.Axis(title="DateTime", labelColor='black', titleColor='black')),
            y=alt.Y('Wind Speed:Q', axis=alt.Axis(title='Wind Speed (m/s)', labelColor='black', titleColor='black'))
        ).properties(
            background='white'
        ).configure_axis(
            labelColor='black',
            titleColor='black'
        )

    return line_chart

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
        
        #Occurs when new day is detected. new file has not been created by PostProcess.py
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

def get_filelist(directory):
    """
    Retrieves and returns list of files in specified directory. Used with selectbox to get list of processed file list
    """    
    file_list = os.listdir(directory)
    return sorted(file_list)

def get_months_list():
    months = [datetime.date(1900, i, 1).strftime('%B') for i in range(1, 13)]
    return months

def files_bymonth(file_list, chosen_month, chosen_year):
    files = []
    for file_name in file_list:
        try:
            date_str = file_name.split("_")[2].split(".")[0]
            file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if file_date.strftime("%B") == chosen_month and file_date.strftime("%Y") == str(chosen_year):
                files.append(file_name)

        except (IndexError, ValueError):
            continue  # Skip files that don't match the expected naming convention

    return files

def get_yearslist(start_year=1990):
    current_year = datetime.datetime.now().year
    years_list = list(range(current_year, start_year - 1, -1))
    return years_list

st.set_page_config(page_title="Wind Sensor Metstation", layout="wide")
try:
    print("Program Running")
    print("Program start: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    data_folder = "Processed data V4"
    mean_filename = "mean_data_"

    #Header for Streamlit
    st.subheader("Wind Sensor Data", anchor = False)

    a1, a2, a3, a4 = st.columns(4, gap = "small")

    #files and month list
    files_directory = get_filelist(data_folder)
    months = get_months_list()
    years = get_yearslist()

    with a1:
        #To choose true north or platform north - Default True North
        wind_not = st.selectbox(
            "Select Wind notation",
            ("True North", "Platform North"),
            index=0 
        ) 

    with a2:
        month_selected = st.selectbox(
            "Select month",
            months
        )

    with a3:
        year_selected = st.selectbox(
            label="Select year",
            options=years
        )
    
    with a4:
        filtered_files = files_bymonth(files_directory, month_selected, year_selected)
        # Create a ZIP archive of the filtered files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_name in filtered_files:
                file_path = os.path.join(data_folder, file_name)
                zipf.write(file_path, arcname=file_name)
        zip_buffer.seek(0)

        st.download_button(
            label="Download ZIP",
            data= zip_buffer,
            file_name=f"{month_selected}_files.zip",
            mime="application/zip"
        )
    
        if st.button('Refresh File List'):
            st.rerun()

    #placeholders for data columns
    col1, col2, col3 = st.columns(3, gap = "small")
    display_1min_speed = col1.metric("1min - Wind Speed (m/s)", np.nan, "-", "off")
    display_1min_direction = col1.metric("1min - Wind Direction (°)", np.nan, "-", "off")
    display_1min_gust = col1.metric("1min - 3s Wind Gust (m/s)", np.nan, "-", "off")

    display_10min_speed = col2.metric("10min - Wind Speed (m/s)", np.nan, "-", "off")
    display_10min_direction = col2.metric("10min - Wind Direction (°)", np.nan, "-", "off")
    display_10min_gust = col2.metric("10min - 3s Wind Gust (m/s)", np.nan, "-", "off")

    #Placeholder for Wind plot (1 minute update using 10min avg data)
    with col3:
        wind_plot_placeholder = st.empty()
        plot_text_placeholder = st.empty()
    
    ################################ Historical Data plots ################################
    st.subheader("Historical Data Representation", anchor = False, divider= "orange")
    col1, col2, col3, col4= st.columns(4, gap = "small")

    with col1:
        st.markdown("Past 1 hour")
        wind_1hour_placeholder = st.empty()
        text_1hour_placeholder = st.empty()
    
    with col2:
        st.markdown("Past Day")
        wind_1day_placeholder = st.empty()
        text_1day_placeholder = st.empty()
    
    with col3:
        st.markdown("Past 7 Days")
        wind_7days_placeholder = st.empty()
        text_7days_placeholder = st.empty()
    
    with col4:
        st.markdown("Past 30 days")
        wind_30days_placeholder = st.empty()
        text_30days_placeholder = st.empty()

    ################################ Time series plots ################################
    st.subheader("Wind Speed Time-Series Representation", anchor = False, divider= "orange")
    col1, col2, col3, col4= st.columns(4, gap = "small")
    
    with col1:
        st.markdown("Past 1 hour")
        wstime_1hour_placeholder = st.empty()
        wstext_1hour_placeholder = st.empty()
    
    with col2:
        st.markdown("Past Day")
        wstime_1day_placeholder = st.empty()
        wstext_1day_placeholder = st.empty()
    
    with col3:
        st.markdown("Past 7 Days")
        wstime_7days_placeholder = st.empty()
        wstext_7days_placeholder = st.empty()

    with col4:
        st.markdown("Past 30 days")
        wstime_30days_placeholder = st.empty()
        wstext_30days_placeholder = st.empty()

    for i in range(3):
        st.markdown(" ")
    footer_html = """
    <div style='text-align: center;'>
    <p>Developed and designed by <a href='https://my.linkedin.com/in/faisal-hasbi-032b31248'>Faisal Hasbi</a>, with early contributions from <a href='https://www.linkedin.com/in/irfan-syafi/'>Irfan Syafi</a></p>
    </div>
    """
    footer_placeholder = st.empty()

    #Variables to define
    last_minute = datetime.datetime.now().minute
    last_hour = datetime.datetime.now().hour
    count_1hour = 1

    plot_speed_1hour = []
    plot_dir_1hour = []

    previous_date = datetime.date.today()

    ################################ Main loop ################################
    while True:
        footer_placeholder.markdown(footer_html, unsafe_allow_html=True)
        current_date = datetime.date.today()
        current_date_str = current_date.strftime("%Y-%m-%d")
        current_minute = datetime.datetime.now().minute
        current_hour = datetime.datetime.now().hour

        if current_date != previous_date:
            time.sleep(20)
            previous_date = current_date

        #Opening mean file path
        mean_path = os.path.join(data_folder, generate_filename(mean_filename))
        
        #Reading mean data
        mean_df = get_data(mean_path)
        mean_df['DateTime'] = pd.to_datetime(mean_df["DateTime"])

        ################################ Display of data ################################
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

            #Wind dial plot - 1 min update
            if pd.notna(windspeed_10min) and pd.notna(winddirection_10min):
                plot_speed_1min = []
                plot_dir_1min = []

                if wind_not == "True North":
                    plot_speed_1min = np.append(plot_speed_1min , windspeed_10min)
                    plot_dir_1min = np.append(plot_dir_1min , winddirection_10min)
                    wind_plot(plot_dir_1min, plot_speed_1min, mode="1min")
                
                elif wind_not == "Platform North":
                    plot_speed_1min = np.append(plot_speed_1min , windspeed_10min)
                    plot_dir_1min = np.append(plot_dir_1min , winddirection_10min_platnorth)
                    wind_plot(plot_dir_1min, plot_speed_1min, mode="1min")                    
                    
                wind_plot_placeholder.image("1min.jpg",use_column_width = "auto")

            else:
                wind_plot(mode="empty")
                wind_plot_placeholder.image("empty.jpg",use_column_width = "auto")

            update_min = datetime.datetime.now().strftime("%H:%M:00")     
            plot_text_placeholder.markdown(f"Last Updated: {update_min}")

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

            wind_plot(mode="empty")
            wind_plot_placeholder.image("empty.jpg",use_column_width = "auto")
        
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

        #Display of 1 hour data
        if len(mean_df) >= 62:

            if len(plot_speed_1hour) < 60 and len(plot_dir_1hour) < 60:
                update_hour = datetime.datetime.now().strftime("%H:%M:00")
                plot_speed_1hour = []
                plot_dir_1hour = []
                plot_datetime_1hour = []

                wind_dir_1hour = mean_df["Wind Direction - Deg (1 min)"].iloc[-62:-2]
                wind_dir_1hour_platnorth = mean_df["Wind Direction - Deg (1 min) Platform North"].iloc[-62:-2]

                if wind_not == "True North":
                    plot_dir_1hour = wind_dir_1hour.tolist()
                
                elif wind_not == "Platform North":
                    plot_dir_1hour = wind_dir_1hour_platnorth.tolist()

                plot_speed_1hour = mean_df["Wind Speed - m/s (1 min)"].iloc[-62:-2].tolist()
                plot_datetime_1hour = mean_df["DateTime"].iloc[-62:-2].tolist()

                #Ensure no NaN values and clean data
                plot_speed_1hour = pd.to_numeric(plot_speed_1hour, errors = "coerce")
                plot_dir_1hour = pd.to_numeric(plot_dir_1hour, errors = 'coerce')
                plot_df = pd.DataFrame({
                    "Wind speed": plot_speed_1hour,
                    "Wind direction": plot_dir_1hour,
                    "Datetime": plot_datetime_1hour
                })
                plot_df.dropna(subset=["Wind direction"], inplace=True)
            
                plot_speed_1hour = plot_df["Wind speed"].values
                plot_dir_1hour = plot_df["Wind direction"].values
                plot_datetime_1hour = plot_df["Datetime"].values

                #Wind Rose plot
                if len(plot_dir_1hour) == 0 or np.all(plot_speed_1hour == 0):
                    wind_plot(mode="empty")
                    wind_1hour_placeholder.image("empty.jpg", use_column_width = "auto")

                    data_1hr = pd.DataFrame({
                        "DateTime": [],
                        "Wind Speed": []
                    })
                else:
                    wind_plot(plot_dir_1hour, plot_speed_1hour, mode="1hour")
                    wind_1hour_placeholder.image("1hour.jpg", use_column_width = "auto")

                    data_1hr = pd.DataFrame({
                        "DateTime": plot_datetime_1hour,
                        "Wind Speed": plot_speed_1hour
                    })
                text_1hour_placeholder.markdown(f"Last Updated: {update_hour}")
                
                #Time plot
                ws1hr_lc = ws_time(data_1hr)
                wstime_1hour_placeholder.altair_chart(ws1hr_lc, use_container_width = True)
                wstext_1hour_placeholder.markdown(f"Last Updated: {update_hour}")
            
            #To check if its a new hour
            if current_hour != last_hour:
                update_hour = datetime.datetime.now().strftime("%H:%M:00")
                last_hour = current_hour

                plot_speed_1hour = []
                plot_dir_1hour = []
                plot_datetime_1hour = []

                wind_dir_1hour = mean_df["Wind Direction - Deg (1 min)"].iloc[-62:-2]
                wind_dir_1hour_platnorth = mean_df["Wind Direction - Deg (1 min) Platform North"].iloc[-62:-2]

                if wind_not == "True North":
                    plot_dir_1hour = wind_dir_1hour.tolist()
                
                elif wind_not == "Platform North":
                    plot_dir_1hour = wind_dir_1hour_platnorth.tolist()

                plot_speed_1hour = mean_df["Wind Speed - m/s (1 min)"].iloc[-62:-2].tolist()
                plot_datetime_1hour = mean_df["DateTime"].iloc[-62:-2].tolist()

                #Ensure no NaN values and clean data
                plot_speed_1hour = pd.to_numeric(plot_speed_1hour, errors = "coerce")
                plot_dir_1hour = pd.to_numeric(plot_dir_1hour, errors = 'coerce')

                plot_df = pd.DataFrame({
                    "Wind speed": plot_speed_1hour,
                    "Wind direction": plot_dir_1hour,
                    "Datetime": plot_datetime_1hour
                })
                plot_df.dropna(subset=["Wind direction"], inplace=True)

                plot_speed_1hour = plot_df["Wind speed"].values
                plot_dir_1hour = plot_df["Wind direction"].values
                plot_datetime_1hour = plot_df["Datetime"].values

                #Wind Rose plot
                if len(plot_dir_1hour) == 0 or np.all(plot_speed_1hour == 0):
                    wind_plot(mode="empty")
                    wind_1hour_placeholder.image("empty.jpg", use_column_width = "auto")

                    data_1hr = pd.DataFrame({
                        "DateTime": [],
                        "Wind Speed": []
                    })

                else:
                    wind_plot(plot_dir_1hour, plot_speed_1hour, mode="1hour")
                    wind_1hour_placeholder.image("1hour.jpg", use_column_width = "auto")

                    data_1hr = pd.DataFrame({
                        "DateTime": plot_datetime_1hour,
                        "Wind Speed": plot_speed_1hour
                    })
                text_1hour_placeholder.markdown(f"Last Updated: {update_hour}")

                ws1hr_lc = ws_time(data_1hr)
                wstime_1hour_placeholder.altair_chart(ws1hr_lc, use_container_width = True)
                wstext_1hour_placeholder.markdown(f"Last Updated: {update_hour}")

        #not enough data must wait for more & plots empty plot
        else:
            if count_1hour == 1:
                wind_plot(mode= "empty")
                wind_1hour_placeholder.image("empty.jpg", use_column_width = "auto")
                text_1hour_placeholder.markdown("Error: Insufficient data for plot")
                count_1hour += 1

                #Time series plot - Wind speed and direction
                data_1hr = pd.DataFrame({
                    "DateTime": [],
                    "Wind Speed": []
                })

                ws1hr_lc = ws_time(data_1hr)
                wstime_1hour_placeholder.altair_chart(ws1hr_lc, use_container_width = True)
                wstext_1hour_placeholder.markdown("Error: Insufficient data for plot")

        #Past day calculation
        previous_date = current_date - timedelta(days=1)

        #Past day representation
        previous_date_str = previous_date.strftime("%Y-%m-%d")
        past_name = f"mean_data_{previous_date_str}.txt"
        past_day_path = os.path.join(data_folder, past_name)

        #Check if past day file exists 
        if not os.path.exists(past_day_path):
            wind_plot(mode= "empty")
            wind_1day_placeholder.image("empty.jpg", use_column_width = "auto")
            text_1day_placeholder.markdown("Error: File does not exist...")

            #Time series plot - Wind speed and direction
            data_1day = pd.DataFrame({
                "DateTime": [],
                "Wind Speed": []
            })
            ws1day_lc = ws_time(data_1day, mode = "1 day")
            wstime_1day_placeholder.altair_chart(ws1day_lc, use_container_width = True)
            wstext_1day_placeholder.markdown("Error: File does not exist...")

        else:
            past_df = pd.read_csv(past_day_path, sep = '\t')
            past_df = past_df.dropna(subset=["Wind Direction - Deg (1 min)"])

            wd_1day = past_df["Wind Direction - Deg (1 min)"].values
            wd_1day_platnorth = past_df["Wind Direction - Deg (1 min)"].apply(calc_platnorth).values
            ws_1day = past_df["Wind Speed - m/s (1 min)"].values
            datetime_1day = past_df["DateTime"].values

            #Ensure no NaN values
            wd_1day = pd.to_numeric(wd_1day, errors = "coerce")
            ws_1day = pd.to_numeric(ws_1day, errors = "coerce")
            wd_1day_platnorth = pd.to_numeric(wd_1day_platnorth, errors = "coerce")

            #Wind plot 1 day
            if wind_not == "True North":
                wind_plot(wd_1day, ws_1day, "1day")
            elif wind_not == "Platform North":
                wind_plot(wd_1day_platnorth, ws_1day, "1day")
            wind_1day_placeholder.image("1day.jpg", use_column_width = "auto")
            text_1day_placeholder.markdown(f"Date: {previous_date}")

            #Time series plot 1 day - Wind speed and direction 
            data_1day = pd.DataFrame({
                "DateTime": datetime_1day,
                "Wind Speed": ws_1day,
            })
            ws1day_lc = ws_time(data_1day, mode = "1 day")
            wstime_1day_placeholder.altair_chart(ws1day_lc, use_container_width = True)
            wstext_1day_placeholder.markdown(f"Date: {previous_date}")

        #To get previous 7 days data - BASED ON MEAN DIRECTORY
        past_7_date_list = [previous_date - timedelta(days=i) for i in range(0, 7)]
        past_7_file_list = [os.path.join(data_folder, mean_filename + str(date) + '.txt') for date in past_7_date_list]
        past_7days_df = pd.DataFrame()

        #To combine past 7 days data into 1 dataframe
        for file_path in past_7_file_list:
            try:
                data = pd.read_csv(file_path, sep = '\t')
                past_7days_df = pd.concat([past_7days_df, data], axis = 0, ignore_index=True)
            except FileNotFoundError: 
                continue
    
        #If no seven days at all - empty plot
        if past_7days_df.empty:
            wind_plot(mode = "empty")
            wind_7days_placeholder.image("empty.jpg", use_column_width = "auto")
            text_7days_placeholder.markdown("Error: Insufficient data for plot")

            #Time series plot 7 days - Wind speed and direction 
            data_7days = pd.DataFrame({
                "DateTime": [],
                "Wind Speed": []
            })
            ws7days_lc = ws_time(data_7days, mode = "7 days")
            wstime_7days_placeholder.altair_chart(ws7days_lc, use_container_width = True)
            wstext_7days_placeholder.markdown("Error: Insufficient data for plot")

        else:
            past_7days_df = past_7days_df.dropna(subset=["Wind Direction - Deg (1 min)"])
            wd_7days = past_7days_df["Wind Direction - Deg (1 min)"].values
            wd_7days_platnorth = past_7days_df["Wind Direction - Deg (1 min)"].apply(calc_platnorth).values
            ws_7days = past_7days_df["Wind Speed - m/s (1 min)"].values
            datetime_7days = past_7days_df["DateTime"].values

            #No NaN values
            wd_7days = pd.to_numeric(wd_7days, errors = "coerce")
            wd_7days_platnorth = pd.to_numeric(wd_7days_platnorth, errors = 'coerce')
            ws_7days = pd.to_numeric(ws_7days, errors = "coerce")

            #Wind plot 7 days
            if wind_not == "True North":
                wind_plot(wd_7days, ws_7days, mode = "7days")
            elif wind_not == "Platform North":
                wind_plot(wd_7days_platnorth, ws_7days, mode = "7days")
            wind_7days_placeholder.image("7days.jpg", use_column_width = "auto")
            text_7days_placeholder.markdown(f"Date: {str(past_7_date_list[-1])} - {str(past_7_date_list[0])}")

            #Time series plot 7 days - Wind speed and direction 
            data_7days = pd.DataFrame({
                "DateTime": datetime_7days,
                "Wind Speed": ws_7days
            })
            ws7days_lc = ws_time(data_7days, mode = "7 days")
            wstime_7days_placeholder.altair_chart(ws7days_lc, use_container_width = True)
            wstext_7days_placeholder.markdown(f"Date: {str(past_7_date_list[-1])} - {str(past_7_date_list[0])}")

        #Past 30 days wind plot
        past_30_date_list = [previous_date - timedelta(days=i) for i in range(0, 30)]
        past_30_file_list = [os.path.join(data_folder, mean_filename + str(date) + '.txt') for date in past_30_date_list]
        past_30days_df = pd.DataFrame()

        #To combine past 30 days data into 1 dataframe
        for file_path in past_30_file_list:
            try:
                data = pd.read_csv(file_path, sep = '\t')
                past_30days_df = pd.concat([past_30days_df, data], axis = 0, ignore_index=True)
            except FileNotFoundError: 
                continue

        #If no 30 days at all - empty plot
        if past_30days_df.empty:
            wind_plot(mode = "empty")
            wind_30days_placeholder.image("empty.jpg", use_column_width = "auto")
            text_30days_placeholder.markdown("Error: Insufficient data for plot")

            #Time series plot 30 days - Wind speed and direction 
            data_30days = pd.DataFrame({
                "DateTime": [],
                "Wind Speed": []
            })
            ws30days_lc = ws_time(data_30days, mode = "30 days")
            wstime_30days_placeholder.altair_chart(ws30days_lc, use_container_width = True)
            wstext_30days_placeholder.markdown("Error: Insufficient data for plot")  

        else:
            past_30days_df = past_30days_df.dropna(subset=["Wind Direction - Deg (1 min)"])
            wd_30days = past_30days_df["Wind Direction - Deg (1 min)"].values
            wd_30days_platnorth = past_30days_df["Wind Direction - Deg (1 min)"].apply(calc_platnorth).values
            ws_30days = past_30days_df["Wind Speed - m/s (1 min)"].values
            datetime_30days = past_30days_df["DateTime"].values

            #No NaN 
            wd_30days = pd.to_numeric(wd_30days, errors = "coerce")
            ws_30days = pd.to_numeric(ws_30days, errors = 'coerce')
            wd_30days_platnorth = pd.to_numeric(wd_30days_platnorth, errors = "coerce")

            #Wind plot
            if wind_not == "True North":
                wind_plot(wd_30days, ws_30days, mode = "30days")
            elif wind_not == "Platform North":
                wind_plot(wd_30days_platnorth, ws_30days, mode = "30days")
            wind_30days_placeholder.image("30days.jpg", use_column_width = "auto")
            text_30days_placeholder.markdown(f"Date: {str(past_30_date_list[-1])} - {str(past_30_date_list[0])}")

            #Time series plot 30 days - Wind speed and direction 
            data_30days = pd.DataFrame({
                "DateTime":datetime_30days,
                "Wind Speed": ws_30days
            })
            ws30days_lc = ws_time(data_30days, mode = "30 days")
            wstime_30days_placeholder.altair_chart(ws30days_lc, use_container_width = True)
            wstext_30days_placeholder.markdown(f"Date: {str(past_30_date_list[-1])} - {str(past_30_date_list[0])}")     

        time.sleep(15) 

except KeyboardInterrupt:
    print("Program ended....")
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Program end: " + end_time)