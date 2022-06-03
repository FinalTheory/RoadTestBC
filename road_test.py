#!/usr/bin/python

import sys
import json
import urllib.request, urllib.error, urllib.parse
import time
import os
import ssl
import http.client
import datetime
import requests
from time import sleep
from dateutil.parser import parse

# keep only the location IDs you need and remove others
TEST_LOCATION_ID = [(2, "Burnaby"), (274, "Burnaby BCIT"), (153, "Langley"), (73, "Port Coquitlam"), (11, "Surrey"), (8, "North Vancouver"), (93, "Richmond")]

# examl type
# 5-R-1: class 5
# 6-R-1: class 6 motorcycle
EXAM_TYPE = "5-R-1"
LAST_NAME = ""
# your driver license ID
DRIVER_LICENSE_ID = ""
# your ICBC keyword
KEYWORD = ""
# the date range that you wanna book road test for
DATE_RANGE = ("2021-09-06", "2021-09-07")

CURL = """
curl 'https://onlinebusiness.icbc.com/deas-api/v1/web/verifyOTP' \
  -X 'PUT' \
  -H 'sec-ch-ua: "Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Referer: https://onlinebusiness.icbc.com/webdeas-ui/booking' \
  -H 'Authorization: %s' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36' \
  -H 'Content-Type: application/json' \
  --data-raw '{"bookedTs":"%s","drvrID":%s,"code":"your-code"}' \
  --compressed
 """

# Fix SSL
if hasattr(ssl, '_create_unverified_context'):
      ssl._create_default_https_context = ssl._create_unverified_context

class Worker(object):
	def __init__(self, last_name, license_id, password):
		self.last_name = last_name
		self.license_id = license_id
		self.password = password
		self.token = None
		self.driver_id = None

	def load_driver_id(self):
		json_body = {"drvrLastName": self.last_name, "licenceNumber": self.license_id}
		headers = {
			"Accept":           "application/json, text/plain, */*",
			"Referer":          "https://onlinebusiness.icbc.com/webdeas-ui/driver",
			"Sec-Ch-Ua-Mobile": "?0",
			"User-Agent":       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
			"Content-Type":     "application/json",
			"Authorization": self.token
		}
		r = requests.put("https://onlinebusiness.icbc.com/deas-api/v1/web/driver", json=json_body, headers=headers)
		# print(r.text)
		if r.status_code == 200:
			self.driver_id = r.json()["drvrId"]
		else:
			print("ERROR: status code={}".format(r.status_code))
			self.driver_id = None

	def getToken(self):
		try:
			json_body = '{"drvrLastName":"%s","licenceNumber":"%s","keyword":"%s"}' % (self.last_name, self.license_id, self.password)
			headers = {"Expires" : "0" ,"Accept": "application/json, text/plain, */*", "Cache-control" : "no-cache, no-store", "Content-Type" : "application/json",\
						"Referer" : "https://onlinebusiness.icbc.com/webdeas-ui/login;type=driver","User-Agent" : " Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36" \
					}
			conn = http.client.HTTPSConnection('onlinebusiness.icbc.com')
			conn.request('PUT', '/deas-api/v1/webLogin/webLogin', json_body, headers)
			response = conn.getresponse()
			token = response.getheader('Authorization')
			print('get token ', token)
			self.token = token
		except:
			self.token = None

	@staticmethod
	def fiterByDate(appointments):
		for ap in appointments:
			# check 
			dt = parse(ap['appointmentDt']['date'])
			if dt >= parse(DATE_RANGE[0]) and dt < parse(DATE_RANGE[1]):
			# if True:
				return ap
		return None
	
	def lock_exam(self, appointment):
		appointment["drvrDriver"] = {
			"drvrId": self.driver_id
		}
		appointment["instructorDlNum"] = None
		appointment["drscDrvSchl"] = {}
		json_body = appointment
		headers = {
			"Accept":           "application/json, text/plain, */*",
			"Referer":          "https://onlinebusiness.icbc.com/webdeas-ui/driver",
			"Sec-Ch-Ua-Mobile": "?0",
			"User-Agent":       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
			"Content-Type":     "application/json",
			"Authorization": self.token
		}
		r = requests.put("https://onlinebusiness.icbc.com/deas-api/v1/web/lock", json=json_body, headers=headers)
		if r.status_code == 200:
			return True
		else:
			print("LOCK ERROR: status code={}".format(r.status_code))
			return False

	def send_otp(self):
		json_body = {
			"bookedTs": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
			"drvrID": self.driver_id,
			"method": "S"
		}
		headers = {
			"Accept":           "application/json, text/plain, */*",
			"Referer":          "https://onlinebusiness.icbc.com/webdeas-ui/booking",
			"Sec-Ch-Ua-Mobile": "?0",
			"User-Agent":       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
			"Content-Type":     "application/json",
			"Authorization": self.token
		}
		r = requests.post("https://onlinebusiness.icbc.com/deas-api/v1/web/sendOTP", json=json_body, headers=headers)
		print(r.text)
		if r.status_code == 200:
			return True
		else:
			print("LOCK ERROR: status code={}".format(r.status_code))
			return False

	def fetch_road_test(self, pos_id, name):
		json_body = {
			"aPosID": pos_id,
			"examDate": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
			"examType": EXAM_TYPE,
			"ignoreReserveTime": False,
			"lastName": LAST_NAME,
			"licenseNumber": DRIVER_LICENSE_ID,
			"prfDaysOfWeek": "[0,1,2,3,4,5,6]",
			"prfPartsOfDay": "[0,1]"
		}
		
		headers = {
			"Accept":           "application/json, text/plain, */*",
			"Referer":          "https://onlinebusiness.icbc.com/webdeas-ui/booking",
			"Sec-Ch-Ua-Mobile": "?0",
			"User-Agent":       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
			"Content-Type":     "application/json",
			"Authorization": self.token
		}
		r = requests.post("https://onlinebusiness.icbc.com/deas-api/v1/web/getAvailableAppointments", json=json_body, headers=headers)
		# print(r.text)
		if r.status_code == 200:
			appointments = r.json()
			if len(appointments):
				return self.fiterByDate(appointments)
			else:
				return None
		else:
			print("ERROR: status code={}".format(r.status_code))
			return None

	def loop(self):
		counter = 0
		self.getToken()
		self.load_driver_id()
		while True:
			try:
				self.getToken()
				if self.token is None:
					sleep(1)
				else:
					self.work()
				counter += 1
			except Exception as e:
				print("ERROR:{}".format(str(e)))
	

	def work(self):
		for pos_id, name in TEST_LOCATION_ID:
			appointment = self.fetch_road_test(pos_id, name)
			if appointment is not None:
				if self.lock_exam(appointment) and self.send_otp():
					msg = "say 'ICBC appointment booked in {}'".format(name)
					print(appointment)
					print(msg)
					print("Use below command to confirm your booking:")
					print(CURL % (self.token, datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), str(self.driver_id)))
					os.system(msg)
					sys.exit(0)
			else:
				print("Nothing found {}".format(datetime.datetime.now().ctime()))


if __name__ == "__main__":
	Worker(LAST_NAME, DRIVER_LICENSE_ID, KEYWORD).loop()
