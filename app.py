from datetime import datetime
from flask import Flask, render_template, jsonify, request
import pandas as pd
from flask_mail import Mail, Message
import pyodbc
from easy_trilateration.model import Circle
from easy_trilateration.least_squares import easy_least_squares
from itertools import combinations
from scipy.spatial import distance
import numpy as np


app = Flask(__name__)
Stop_map = {
    1: "Dawson Street, Dublin City South",
    2: "Embassy of Malta, Dublin City South",
    3: "Fitzwilliam Place, Dublin City South",
    4: "Grand Parade, Dublin City South",
    5: "Dartmouth Road, Ranelagh",
    6: "Leeson Street Upper, Ranelagh",
    7: "Royal Hospital, Donnybrook",
    8: "Morehampton Terrace, Donnybrook",
    9: "Donnybrook Village, Donnybrook",
    10: "Garda Station, Donnybrook",
    11: "Donnybrook Road, Donnybrook",
    12: "Donnybrook Garage, Donnybrook",
    13: "Teresian School, Donnybrook",
    14: "RTE, Donnybrook",
    15: "Belfield Court, Donnybrook",
    16: "UCD Belfield, Belfield",
    17: "Seafield Road, Belfield",
    18: "St. Thomas Road, Booterstown",
    19: "Booterstown Avenue, Mount Merrion",
    20: "Greenfield Road, Mount Merrion",
    21: "Stillorgan Park Hotel, Mount Merrion",
    22: "Oatlands College, Stillorgan",
    23: "Laurence Road, Stillorgan",
    24: "Merville Road, Stillorgan",
    25: "Brewery Road, Stillorgan",
    26: "Galloping Green, Galloping Green",
    27: "Newtownpark Avenue, Galloping Green",
    28: "Knocksinna, Foxrock",
    29: "Foxrock Church, Foxrock",
    30: "Foxrock Park, Deansgrange",
    31: "Foxrock Avenue, Deansgrange",
    32: "Deansgrange Village, Deansgrange",
    33: "Kill Lane, Deansgrange",
    34: "Holy Family Church, Kill of the Grange",
    35: "IADT Dun Laoghaire, Kill of the Grange",
    36: "Kill Avenue, Kill of the Grange",
    37: "Mounttown Road Lower, Dun Laoghaire",
    38: "Tivoli Terrace South, Dun Laoghaire",
    39: "Knapton Court, Dun Laoghaire",
    40: "Vesey Place, Dun Laoghaire",
    41: "Smith's Villas, Dun Laoghaire",
    42: "St. Michael's Hospital, Dun Laoghaire",
    43: "Dun Laoghaire Shopping Centre, Dun Laoghaire",
    44: "Dun Laoghaire Station, Dun Laoghaire"
}
css_styles = '''
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
'''
metre_to_pxl = 1  # Convert meters to pixels
antennas_in_use = [1,2,3,4]
# antennas_positions = [
#     np.array([610+100, 1042 - 596+100]) * metre_to_pxl,  # white = 1
#     np.array([0+100, 1042+100]) * metre_to_pxl,         # Red = 2
#     np.array([0+100, 1042 - 641+100]) * metre_to_pxl,  # Green = 3
#     np.array([610+100, 1042+100]) * metre_to_pxl  # Blue = 4   
# ]
antennas_positions = [
    np.array([0, 0]) * metre_to_pxl,  # white = 1
    np.array([300, 300]) * metre_to_pxl,  # Red = 2
    np.array([300, 0]) * metre_to_pxl,  # Green = 3
    np.array([0, 300]) * metre_to_pxl # Blue = 4   
]
Table1 = pd.DataFrame({'UUID': [],'Ant1': [],'Ant2': [],'Ant3': [],'Ant4': []})

IsCountDown = False
stop_param = 1
Passenger_count = 0
conn_str = 'DRIVER={SQL Server};SERVER=LAPTOP-9G6EQ1SM;DATABASE=SummitBus;UID=SummitBus;PWD=sa123;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
#flask run --host=0.0.0.0

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 465  # Replace with your SMTP port
app.config['MAIL_USERNAME'] = 'summitbus145@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'dwwjrfpzwxoqnwyj'  # Replace with your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'eidt@tcd.ie'  # Replace with your Gmail email
mail = Mail(app)


#stop_param = request.args.get('stop', type=int, default=0)     

@app.route('/Get_Email')
def Get_Email():
    name = request.args.get("name", type=str, default="1")
    query = "SELECT Email FROM UserMapping where UUID = '" + name + "'"
    cursor.execute(query)
    rows = cursor.fetchall()
    return str(rows[0][0])

@app.route('/POST_API', methods=['POST'])
async def POST_API():
    try:
        global Table1
        data = request.json
        devices = data['Devices']
        df = pd.DataFrame(devices)
        if df.empty == False:
            for count, id in enumerate(df["UUID"].values):
                if id not in Table1["UUID"].values:
                    UUIDval = df.iloc[count]["UUID"]
                    #Send_Email(UUIDval,True)
                    new_row = {'UUID' : UUIDval}
                    Table1 = pd.concat([Table1, pd.DataFrame([new_row])], ignore_index = True)
                else:
                    if df.iloc[count]['Ant'] == 1:
                        Table1.loc[Table1["UUID"]==id, "Ant1"] = df.iloc[count]["rssi"]
                    elif df.iloc[count]['Ant'] == 2:
                        Table1.loc[Table1["UUID"]==id, "Ant2"] = df.iloc[count]["rssi"]
                    elif df.iloc[count]['Ant'] == 3:
                        Table1.loc[Table1["UUID"]==id, "Ant3"] = df.iloc[count]["rssi"]
                    elif df.iloc[count]['Ant'] == 4:
                        Table1.loc[Table1["UUID"]==id, "Ant4"] = df.iloc[count]["rssi"]
            unique = Table1["UUID"][~Table1["UUID"].isin(df["UUID"])].drop_duplicates()
            for id in unique.values:
                #Send_Email(id,False)
                Table1.drop(Table1.loc[Table1["UUID"]==id].index,inplace=True)
            html_table = Table1.to_html(classes='data', header='true')
            #print('\x1b[H\x1b[2J', end='')
            #print(Table1)
            return jsonify({'html_table': f'{css_styles}{html_table}'})
        #if len(Table1) == 1:
            #Send_Email(Table1["UUID"][0],False)
        Table1 = pd.DataFrame({'UUID': [],'Ant1': [],'Ant2': [],'Ant3': [],'Ant4': []})
        return "None"
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route('/get_table_data', methods=['GET'])
def get_table_data():
    try:
        global Table1        
        html_table = Table1.to_html(classes='data', header='true')
        return jsonify({'html_table': f'{css_styles}{html_table}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route('/Update_Stop_Number', methods=['GET'])
def Update_Stop_Number():
    try:
        global stop_param
        global IsCountDown
        if stop_param == 44:
            IsCountDown = True
        elif stop_param == 1:
            IsCountDown = False
        if IsCountDown:
            stop_param = stop_param - 1        
        else:
            stop_param = stop_param + 1
        stop_name = Stop_map[stop_param]
        return jsonify({'stop_param': f'{stop_name}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"
    
@app.route('/Get_bus_details', methods=['GET'])
def Get_bus_details():
    Total_seats = 50
    Free_seats = 0
    global stop_param
    global Table1
    Stop_No = 0
    if IsCountDown:
        Stop_No = stop_param - 1   
    else:
        Stop_No = stop_param + 1  
    Free_seats = Total_seats - len(Table1)
    return jsonify({"Next_stop": Stop_map[Stop_No], "Free_seats": Free_seats})   

@app.route('/Update_Passenger_count', methods=['GET'])
def Update_Passenger_count():
    try:
        global Table1
        return jsonify({'Passenger_count': f'{len(Table1)}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route('/Get_Stop_Number', methods=['GET'])
def Get_Stop_Number():
    try:
        global stop_param
        stop_name = Stop_map[stop_param]
        return jsonify({'stop_param': f'{stop_name}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route('/Get_Table_for_map', methods=['GET'])
def Get_Table_for_map():
    try:
        global Table1
        HasNan = Table1.isnull().values.any()
        if HasNan:
            return jsonify({'Devices': f'{pd.DataFrame()}'})
        table1_str = str(Table1).strip()
        return jsonify({'Devices': f'{table1_str}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route("/")
def home():
    return render_template('Home.html', tables=[Table1.to_html(classes='data', header="true")], name=0)

def Send_Email(UUIDval,IsBoarding):
        query = "SELECT Email FROM UserMapping where UUID = '" + UUIDval + "'"
        cursor.execute(query)
        rows = cursor.fetchall()
        if len(rows) > 0:
            recipients = [row[0] for row in rows]
            if IsBoarding:
                subject = 'Welcome'
                body = 'Welcome onboard summit bus, we hope you enjoy your journey with us!'  
                send_email(subject, recipients, body)                               
            else:
                subject = 'Your fare summary'
                body = 'Thanks for riding with Summit Bus today, your fare is €1'
                send_email(subject, recipients, body)

def send_email(subject, recipients, body):
    msg = Message(subject=subject, recipients=recipients, body=body)
    mail.send(msg)

def convert_rssi_to_m(rssi):
    """ Convert RSSI value to meters. """
    rssi_at_1m = -70  # RSSI value at 1 meter
    N = 4  # Environmental factor
    return 10 ** ((rssi_at_1m - rssi) / (10.0 * N)) * 100

def triangulation(distances):
    """ Perform trilateration based on distances to antennas. """
    antennas = [Circle(pos[0], pos[1], dist) for pos, dist in zip(antennas_positions, distances)]
    result, meta = easy_least_squares(antennas)
    return result

def perform_trilateration(three_antennas, three_distances):
    antennas = [Circle(pos[0], pos[1], dist) for pos, dist in zip(three_antennas, three_distances)]
    result, meta = easy_least_squares(antennas)
    if meta['success']:
        return result
    else:
        return None

@app.route('/Calculate_Position_Coordinates', methods=['GET'])
def Calculate_Position_Coordinates():
    global Table1
    # data1 = {
    #  'UUID': ['0000181c-0000-1000-8000-00805f9b34fb', 'new_uuid_1', 'new_uuid_2'],
    #  'Ant1': [-40, -80, -120],
    #  'Ant2': [-50, -90, -130],
    #  'Ant3': [-60, -100, -140],
    #  'Ant4': [-70, -110, -150]
    #  }
    # df = pd.DataFrame(data1)
    # data = []
    # data.append({"Device_name": "38", "Device_x": 300, "Device_y": 300})
    # return jsonify(data)
    devices = Table1
    _, columns = devices.shape
    if columns == 5:
        data = []
        for _, device in devices.iterrows():
            if not device.isna().any():
                distances = np.array([convert_rssi_to_m(device[f"Ant{i}"]) for i in antennas_in_use])
                min_ant_num = (np.where(distances == distances.min())[0][0])
                print(f"Closest to Ant: {min_ant_num+1}")
                positions_x = []
                positions_y = []
                for combo in combinations(range(4), 3):  # Generate combinations of antenna indices
                    selected_antennas = [antennas_positions[i] for i in combo]
                    selected_distances = [distances[i] for i in combo]
                    position = perform_trilateration(selected_antennas, selected_distances)
                    if position is not None:
                        positions_x.append(position.center.x)
                        positions_y.append(position.center.y)
                min_dist = 1000000
                best_circle = 0
                for count, _ in enumerate(positions_x):
                    c1 = antennas_positions[min_ant_num]
                    c2 = (positions_x[count], positions_y[count])
                    euclidean_distance = distance.euclidean(c1, c2)
                    if euclidean_distance < min_dist:
                        best_circle = count
                        min_dist = euclidean_distance
                print(f"Min Distances: {min_dist} cm")
                count = 0
                device_name = str(device["UUID"])[6:8]
                device_x = abs(int(positions_x[best_circle]))
                device_y = abs(int(positions_y[best_circle]))
                data.append({"Device_name": device_name, "Device_x": device_x, "Device_y": device_y})
                print(data)
        return jsonify(data)
    return "Error"

@app.route('/Is_onboard_bus', methods=['GET'])
def Is_onboard_bus():
    global Table1
    Is_onboard = False
    UUID = request.args.get('UUID', type=str, default="") 
    if UUID == '00002a37-0000-1000-8000-00805f9b34fb':
        return jsonify({'Is_Onboard': f'{True}'})
    if len(Table1) > 0:
        specific_string = UUID
        string_exists = (Table1['UUID'] == specific_string).any()
        if string_exists:
            Is_onboard = True
        else:
            Is_onboard = False
        return jsonify({'Is_Onboard': f'{Is_onboard}'})
    return jsonify({'Is_Onboard': f'{Is_onboard}'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)