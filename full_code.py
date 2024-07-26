import serial, serial.tools.list_ports
import datetime, time
from datetime import timedelta
import pandas as pd
import os, sys
import numpy as np
import math

"""
Configure the sensor BEFOREHAND using techniques specified by manufacturer. See the sensor 
manual for complete list of terminal commands.

## PROGRAM DIRECTORY STRUCTURE:
/Main_folder
├── Mainpage.py
└── full_code.py
└── Postprocess.py
└── Pre-Processed data (Wind data ONLY)
|   └── Raw data files
└── Processed data V4 (Wind data ONLY)
|   └── Processed data files
└── Sensor pages
    └── Windsensor1.py
    └── Other Sensor page scripts

## MAIN SCRIPT FUNCTION:
    -   Receives raw data directly from the wind sensor using a serial (RS-422-USB Converter) line.
    -   Saves data as CSV in a specified folder with the format 'raw_wind_data_{current_date}.txt'.
    -   Calculates U & V wind speed vector components for ease of post-processing.
    -   Method describe in this script be used similarly with different sensors that communicate/transmit 
        data via serial communication.

## NOTE:
    -   The script is designed to run continuously, providing constant data and automatically 
        sorting the output CSV by date. 

    -   When a new day is detected, the script appends 1 hour of data (23:00:00 - 23:59:59) from 
        the previous day to the new day's CSV for post-processing continuity.

    -   script stops using Keyboard Interrupt (Ctr + C).

    -   To identify sensor serial port use  serial.tools.list_ports method (connect sensor first).
        Read more here:https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python.

    -   To calculate U&V components of windspeed, refer:
        •   U = component from south to north
        •   V = component form east to west

## TECHNICAL SPECIFICATIONS:
    -   Sensor name: Gill Instruments - WindObserver II
    -   Output string format: NMEA Ascii IIMWV (See sensor manual)
    -   Baud rate = 9600
    -   Output frequency = 1 Hz (1 output/sec)
    -   Sensor configuration method: Any Terminal Emulator software (e.g. PuTTY)

See sensor manual & PETRONAS Offshore manual for further technical specifications.

## TODO: 
    -   Add way to test output string of sensor; test output for first time use.
        Example NMEA Ascii string output: "$IIMWV, 129, R, 002.10, M, A*, CC
    -   Add more intuitive more to stop script.

## REFERENCES
    -   Pyserial Documentation: https://pyserial.readthedocs.io/en/latest/

"""

def check_sensor(data, sensor_path):
    """
    Used to determine the status of the sensor and ensure correct operation of code.

    If no data detected (sensor turned off), function calculates off duration until
    data is detected again (sensor turn back on).

    Returns True when data is detected from sensor
    """

    global sensor_off_count, sensor_status, sensor_off_timestamp, sensor_on_timestamp, duration, sensor_timestampoff

    if data: 
        #Sensor previously Off, Sensor now On
        if sensor_status == False:
            print("\nSensor is back online.")
            sensor_timestampon = datetime.datetime.now()
            sensor_on_timestamp.append(sensor_timestampon.strftime("%Y-%m-%d %H:%M:%S"))
            
            duration_calc = sensor_timestampon - sensor_timestampoff
            duration.append(duration_calc)

            #Create CSV file for sensor status
            df_sensor = pd.DataFrame({
                "Sensor Off Time Stamp": sensor_off_timestamp,
                "Sensor Back On Time Stamp": sensor_on_timestamp,
                "Duration": duration
            })
        
            df_sensor.to_csv(sensor_path, sep = '\t', mode = 'a', index=False, header = not os.path.exists(sensor_path))


            #Appending blank data into lists
            if sensor_off_timestamp:
                duration_seconds = duration_calc.total_seconds()

                for i in range(int(duration_seconds)):
                    update_blank(sensor_timestampoff + datetime.timedelta(seconds = i))

            # Clear lists for the next update
            sensor_off_timestamp.clear()
            sensor_on_timestamp.clear()
            duration.clear()

            #Change sensor status to being on
            sensor_status = True

        return True
    
    else:
        #Sensor previously On, Sensor now Off
        if sensor_status == True:
            sensor_timestampoff = datetime.datetime.now()
            sensor_off_timestamp.append(sensor_timestampoff.strftime("%Y-%m-%d %H:%M:%S"))
            sensor_off_count += 1

            #To update data with current blank data
            update_blank(sensor_timestampoff)

            sensor_status = False
        
        print("\nError: No data received. Check sensor status")

def update_blank(timestamp):
    """
    Used with check_sensor to update data csv with nan data when sensor is off
    """
    # Used to append Nan data to main data lists 
    global time_list, wind_direction, wind_speed, u_comp_list, v_comp_list

    timestamp = str(timestamp).split(".")[0]
    time_list.append(timestamp)
    wind_direction.append(np.nan)
    wind_speed.append(np.nan)
    u_comp_list.append(np.nan)
    v_comp_list.append(np.nan)
      
def list_port():
    """
    Returns a list of com ports in device with a brief description
    """

    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    return available_ports

def initiallize_serial(serial_port , baud_rate):
    """
    Initiallizes serial port and opens port for communication. Defines object 
    serial.Serial and port location and baud rate of sensor. 

    Necessary for estalbishing serial connection between device and sensor. script
    stops if no serial port with defined name is found.

    returns ser - opened port that receives data
    """

    try:
        ser = serial.Serial(
            port = serial_port,
            baudrate = baud_rate,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            timeout = 1
        )
                
        if not ser.isOpen():
            ser.open()

        print("\nSerial port is open")
        time.sleep(0.5)
        print(".")
        time.sleep(0.5)
        print(".")
        time.sleep(0.5)
        print(".")            
        time.sleep(0.5)
        print(".")
        time.sleep(0.5)
        print("\nConnected to: " + ser.name)
        time.sleep(0.5)

        ser.reset_input_buffer()#to clear the queue
        return ser

    except serial.SerialException as e:
        print(f"Error: {e}")
        sys.exit("Exited...")

def update_data(data_path):
    """
    Updates/appeneds new raw data CSV with real time data from sensor. After every update, 
    data is cleared from lists to make room for new data.
    """

    df_rd = pd.DataFrame({
    "DateTime": time_list,
    "WindDirection (Deg)": wind_direction,
    "WindSpeed (m/s)": wind_speed,
    "U": u_comp_list,
    "V": v_comp_list
    })

    # Convert DataFrame to TXT file, appending data if the file exists
    df_rd.to_csv(data_path, sep='\t', mode='a', index=False, header = not os.path.exists(data_path))

    # Clear lists for the next update
    time_list.clear()
    wind_direction.clear()
    wind_speed.clear()
    u_comp_list.clear()
    v_comp_list.clear()

def create_csv(wind_path, sensor_path):
    """
    Creates CSV files based on given path files
    """

    if not os.path.exists(wind_path):
        print("\nCSV file does not exist....")
        with open(wind_path, 'w') as f:
            f.write("DateTime\tWindDirection (Deg)\tWindSpeed (m/s)\tU\tV\n")
        print("CSV file created....")
    
    if not os.path.exists(sensor_path):
          with open(sensor_path, 'w') as f:
            f.write("Sensor Off Time Stamp\tSensor Back On Time Stamp\tDuration\n")      

def generate_filename(file_name):
    """
    Returns file_name as string that contains file name and current date
    """

    current_date = datetime.date.today().strftime("%Y-%m-%d")
    return f"{file_name}_{current_date}.txt"

# Specify serial port and baud rate - baud rate based on sensor requirements
serial_port = "/dev/ttyUSB0"  
baud_rate = 9600

data_folder = "Pre-Processed data"
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

sensor_folder = "Sensor Status"
if not os.path.exists(sensor_folder):
    os.makedirs(sensor_folder)

#Port information
available_ports = list_port()
print("Available Ports:")
for a in available_ports:
    print(a)

#script stops when defined serial_port is not in listed ports
if serial_port not in available_ports:
    print(f"Error: {serial_port} is not available/connected. Reconnect Com port to allow program to continue....")
    sys.exit('Exited...')

ser = initiallize_serial(serial_port, baud_rate)

program_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("Program start: " + program_start)

#Wind data csv
time_list = []
wind_direction = []
wind_speed = []

w_radian_list = []
u_comp_list = []
v_comp_list = []

sensor_status = True
sensor_off_timestamp = []
sensor_on_timestamp = []
duration = []
sensor_off_count = 0

previous_date = datetime.date.today() #Initiallize when first start

try:
    while True:

        #Always updating
        current_date = datetime.date.today()
        raw_data_path = os.path.join(data_folder, generate_filename("raw_wind_data"))
        sensor_status_path = os.path.join(sensor_folder, generate_filename("sensor_status"))
        
        create_csv(raw_data_path, sensor_status_path)

        #updating with previous day data - only occurs when new day passes
        if current_date != previous_date:
            previous_date_str = previous_date.strftime("%Y-%m-%d")
            past_direc = "Pre-Processed data"
            past_name = f"raw_wind_data_{previous_date_str}.txt"
            past_day_path = os.path.join(past_direc, past_name)

            #To get last 1 hour data 
            pday_df = pd.read_csv(past_day_path, sep = '\t')
            pday_df["DateTime"] = pd.to_datetime(pday_df['DateTime'])

            pday_data = pday_df.loc[(pday_df["DateTime"]  >= 
                                    datetime.datetime.strptime(str(previous_date) + ' 23:00:00', '%Y-%m-%d %H:%M:%S')) 
                                    & (pday_df['DateTime'] <= 
                                    datetime.datetime.strptime(str(previous_date) + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
                                    ]
            new_day_df = pd.read_csv(raw_data_path, sep = '\t')
            new_day_df = pd.concat([pday_data, new_day_df], ignore_index = True, axis = 0)
            new_day_df.to_csv(raw_data_path, sep='\t', index=False)

            previous_date = current_date  
    
        #Reading data from Moxa Cable - 1s rate
        raw_data = ser.readline()
        if check_sensor(raw_data, sensor_status_path):
            raw_data = raw_data.decode().strip() 
            data_split = raw_data.split(',')

            #Wind direction and speed
            wd = data_split[1]
            wind_direction.append(int(wd))
            ws = data_split[3]
            wind_speed.append(float(ws))

            #Calculating radian & UV components
            w_radian = math.radians(float(wd))
            w_radian_list.append(w_radian)

            u_comp = -float(ws) * math.cos(w_radian) # U = component from south to north
            u_comp_list.append(round(u_comp,4))
            v_comp = -float(ws) * math.sin(w_radian) # V = component form east to west
            v_comp_list.append(round(v_comp, 4))
                
            #Timestamps
            time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_list.append(time_now)

            update_data(raw_data_path)
            print(raw_data) #Prints received NMEA string from sensor

except KeyboardInterrupt:
    update_data(raw_data_path)
    ser.close()
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\nExiting........")
    print("Program end: " + end_time)
    print(f"Sensor has been off for {sensor_off_count} times")