from datetime import datetime
from flask import Flask, render_template, jsonify, request
import bluetooth
import pandas as pd
import numpy as np
from flask_mail import Mail, Message
import pyodbc
from bleak import BleakScanner
import json

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

Table1 = pd.DataFrame({'UUID': [],'Ant1': [],'Ant2': [],'Ant3': [],'Ant4': []})

stop_param = 0
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
        #Table1 = pd.DataFrame({'UUID': [],'Ant1': [],'Ant2': [],'Ant3': [],'Ant4': []})
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


@app.route('/Get_Table_for_map', methods=['GET'])
def Get_Table_for_map():
    try:
        global Table1
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)