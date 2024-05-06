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
metre_to_pxl = 0.5  # Convert meters to pixels
antennas_in_use = [1,2,3,4]
antennas_positions = [
    np.array([610+100, 1042 - 596+100]) * metre_to_pxl,  # white = 1
    np.array([0+100, 1042+100]) * metre_to_pxl,         # Red = 2
    np.array([0+100, 1042 - 641+100]) * metre_to_pxl,  # Green = 3
    np.array([610+100, 1042+100]) * metre_to_pxl  # Blue = 4   
]
Table1 = pd.DataFrame({'UUID': [],'Ant1': [],'Ant2': [],'Ant3': [],'Ant4': []})

stop_param = 0
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

# @app.route('/get_updated_data')
# async def get_updated_data():
#     try:
#         global stop_param 
#         stop_param = request.args.get('stop', type=int, default=0)     

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
        stop_param = stop_param + 1
        return jsonify({'stop_param': f'{stop_param}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route('/Get_Passenger_Count', methods=['GET'])
def Get_Passenger_Count():
    try:
        global Passenger_count        
        return jsonify({'Passenger_count': f'{Passenger_count}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"

@app.route('/Update_Passenger_count', methods=['GET'])
def Update_Passenger_count():
    try:
        global Table1
        print(len(Table1))
        return jsonify({'Passenger_count': f'{len(Table1)}'})
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return "None"




@app.route('/Get_Stop_Number', methods=['GET'])
def Get_Stop_Number():
    try:
        global stop_param
        return jsonify({'stop_param': f'{stop_param}'})
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
    rssi_at_1m = -75  # RSSI value at 1 meter
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
    # 'UUID': ['0000181c-0000-1000-8000-00805f9b34fb', 'new_uuid_1', 'new_uuid_2'],
    # 'Ant1': [-40, -80, -120],
    # 'Ant2': [-50, -90, -130],
    # 'Ant3': [-60, -100, -140],
    # 'Ant4': [-70, -110, -150]
    # }
    #df = pd.DataFrame(data1)
    devices = Table1
    _, columns = devices.shape
    if columns == 5:
        device_name = []
        device_x = []
        device_y = []
        data = {}
    #if not devices.empty:
        color_count = 0
        for _, device in devices.iterrows():
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
            device_name.append(str(device["UUID"])[6:8])
            device_x.append(int(positions_x[best_circle]))
            device_y.append(int(positions_y[best_circle]))
            data = {
            "Device_name": device_name,
            "Device_x": device_x,
            "Device_y": device_y
            }
            print(data)
        return jsonify(data)
    return "Error"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)