from flask import Flask, Response
import datetime
import pyodbc
import time
import schedule
import threading

from flask import render_template, redirect, url_for, request, json, jsonify, Response, session
import requests
app = Flask(__name__)
NUM_DAYS = 2
#user_contacts = []
#user_pincode = []
@app.route('/')
def home():

	return render_template('home.html')

@app.route('/get_user_data')
def get_user_data():
	user_contact = []
	user_pincode = []

	SQL = "SELECT [ContactNumber],[Pincode] FROM [dbo].[UserData]"
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=abc;UID=sa;PWD=Hello@123')
	cursor = cnxn.cursor()
	cursor.execute("SELECT [ContactNumber],[Pincode] FROM [dbo].[UserData] where [MessageSent] != ?", True)

	for row in cursor.fetchall():
		print("row ", row)
		user_contact.append(str(row[0]))
		user_pincode.append(str(row[1]))

	user_data = {}
	user_data["contact"] = user_contact
	user_data["pincode"] = user_pincode

	return user_data;


@app.route('/userData', methods=['POST'])
def userData():

	PhoneNumber = request.form["PhoneNumber"]
	Pincode = (request.form["Pincode"])
	age = (request.form["age"])
	mesage_sent = False
    #print("enter")

	print("enter")
    #SQL = "INSERT INTO [dbo].[UserData]([ContactNumber],[Pincode], [MessageSent])VALUES('" + PhoneNumber + "','" + Pincode + "','" + mesage_sent + ")"
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=abc;UID=sa;PWD=Hello@123')
	cursor = cnxn.cursor()
	cursor.execute("INSERT INTO [dbo].[UserData]([ContactNumber],[Pincode],[Age], [MessageSent])VALUES(?, ?, ?,?)", PhoneNumber, Pincode,age ,mesage_sent)
	cursor.commit()
	cnxn.close()

	send_message(PhoneNumber, Pincode, True)
	return "success"


def get_slot_by_pincode():
	print("get_slot_by_pincode ", str(datetime.datetime.today()))
	Pincode = get_user_info_from_db.user_pincode
	PhoneNumbers = get_user_info_from_db.user_contacts
	age = get_user_info_from_db.age
	new_user = False
	base = datetime.datetime.today()
	date_list = [base + datetime.timedelta(days=x) for x in range(NUM_DAYS)]
	date_str = [x.strftime("%d-%m-%Y") for x in date_list]
	users_data_length = len(PhoneNumbers)
	#send_message(PhoneNumber, Pincode, new_user)
	print("PhoneNumbers ", PhoneNumbers)
	print("Pincode ", Pincode)

	user_message_sent = []

	for i in range(users_data_length):
			for INP_DATE in date_str:
				URL = "http://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={}&date={}".format(Pincode[i], INP_DATE)
				headers = {
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
}
				response = requests.get(URL, headers=headers)
				print("response ", response)
				if response.ok:
					resp_json = response.json()
					session_len = len(resp_json["sessions"])
					print(resp_json["sessions"])
					if ((session_len != 0) and (PhoneNumbers[i] not in user_message_sent)) :
						for z in range(session_len):
							if(resp_json["sessions"][z]["min_age_limit"] == int(age[i]) and (PhoneNumbers[i] not in user_message_sent)):
								print("availability")
								send_message(PhoneNumbers[i], Pincode[i],False)
								user_message_sent.append(PhoneNumbers[i])
								z = session_len


def send_message(PhoneNumber, Pincode, new_user):

	url = "https://www.fast2sms.com/dev/bulkV2"

	if(new_user == True):
		payload = "message=Hi,You will get message for session availability, in area " + str(Pincode) +"&language=english&route=q&numbers=" + str(PhoneNumber)
	else:
		payload = "message=Hi,Session Available in area " + str(Pincode) +"&language=english&route=q&numbers=" + str(PhoneNumber)

		cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=abc;UID=sa;PWD=Hello@123')
		cursor = cnxn.cursor()
		cursor.execute("Update [dbo].[UserData] SET [MessageSent] = ? Where [ContactNumber] = ? ", True, PhoneNumber)
		cursor.commit()
		cnxn.close()

	print("payload sent", payload + "    " +  str(datetime.datetime.today()))
	headers = {
		'authorization': "eHdRKZmB6lQr5pA17Ds23iaEJ0hSkLGMU8cyNCY4IfXW9btuPT2oKRHX1rOvENAldCzSfxpQLW9eIYh3",
		'Content-Type': "application/x-www-form-urlencoded",
		'Cache-Control': "no-cache",
		}

	response = requests.request("POST", url, data=payload, headers=headers)
	get_user_info_from_db()
	print("mesage response ", response)

def get_user_info_from_db():
	print("get_user_info_from_db ", str(datetime.datetime.today()))
	get_user_info_from_db.user_pincode = []
	get_user_info_from_db.user_contacts = []
	get_user_info_from_db.age = []

	SQL = "SELECT [ContactNumber],[Pincode],[Age] FROM [dbo].[UserData]"
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=abc;UID=sa;PWD=Hello@123')
	cursor = cnxn.cursor()
	cursor.execute("SELECT [ContactNumber],[Pincode],[Age] FROM [dbo].[UserData] where [MessageSent] != ?", True)

	#print("currr  ", cursor.fetchall())
	for row in cursor.fetchall():
		get_user_info_from_db.user_contacts.append(str(row[0]))
		get_user_info_from_db.user_pincode.append(str(row[1]))
		get_user_info_from_db.age.append(str(row[2]))
	cnxn.close()

def schedule_fetch_data_query():
	print("schedule_fetch_data_query")
	schedule.every(5).hours.do(get_user_info_from_db)

	while True:
		schedule.run_pending()
		#time.sleep(1)

def schedule_check_vaccination_slot():
	print("schedule_check_vaccination_slot")
	schedule.every(1).minutes.do(get_slot_by_pincode)

	#while True:
		#schedule.run_pending()
		#time.sleep(1)



thread1 = threading.Thread(target = schedule_fetch_data_query, args = ())
thread1.setDaemon(True)
thread1.start()
#thread1.join()
thread2 = threading.Thread(target = schedule_check_vaccination_slot, args = ())
thread2.setDaemon(True)
thread2.start()
#thread2.join()

get_user_info_from_db()

if __name__ == '__main__':
	app.run(host='15.77.10.155', port=int("4000"))
