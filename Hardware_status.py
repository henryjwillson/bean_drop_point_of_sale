import subprocess
import time
import _thread
from ThermalPrinterRaspi2 import *
import requests 	#Used to check internet connection
import serial


#Modules imported during testing
import multiprocessing
import concurrent.futures
from multiprocessing import Pool
from Screen_Numbers_Class import screen_numbers



class hardware_status:
	'''This class represents the status of hardware on the Point of Sale System'''
	
	def __init__(self, RFID_status, Camera_status, Printer_status, Wifi_status, refresh_count, updated_hardware_status):
		self.RFID_status = RFID_status
		self.Camera_status = Camera_status
		self.Printer_status = Printer_status
		self.Wifi_status = Wifi_status 
		self.refresh_count = refresh_count
		self.updated_hardware_status = updated_hardware_status
		
	def __str__(self):
		return 'RFID: %s , Camera: %s , Printer: %s , Wifi: %s , Refresh Count: %s' % (self.RFID_status, self.Camera_status, self.Printer_status, self.Wifi_status, self.refresh_count)
		
	def RFID_status_check_method(self):
		current_status = self.RFID_status
		try:
			p1 = subprocess.run(["./rfidb1-tool /dev/ttyS0 getmoduleversion"], capture_output=True, cwd="/home/pi/rfidb1-tool_v1.1", shell=True)
			print(p1.stdout.decode())
			if p1.stdout.decode()[0:10] == "Version is":
				print("True response found")
				self.RFID_status = True
				print("The new RFID Status is: ", self.RFID_status)
				if current_status != self.RFID_status:
					self.updated_hardware_status = True
				return True
			else:
				self.RFID_status = False
				print("RFID status failure")
				if current_status != self.RFID_status:
					self.updated_hardware_status = True
				return False
		except Exception as e:
			print(e)
			print("RFID status failure")
			self.RFID_status = False
			if current_status != self.RFID_status:
					self.updated_hardware_status = True
			return False
			
	def Camera_status_check_method(self):
		current_status = self.Camera_status
		try:
			p1 = subprocess.run(["vcgencmd get_camera"], capture_output=True, shell=True)
			print(p1.stdout.decode())
			if p1.stdout.decode()[0:22] == "supported=1 detected=1":
				print("True response found")
				self.Camera_status = True
				print("The new Camera Status is: ", self.RFID_status)
				if current_status != self.Camera_status:
					self.updated_hardware_status = True
				return True
			else:
				self.Camera_status = False
				if current_status != self.Camera_status:
					self.updated_hardware_status = True
				return False
		except Exception as e:
			print(e)
			self.Camera_status = False
			if current_status != self.Camera_status:
					self.updated_hardware_status = True
			return False
			
	def internet_connection_check(self):
		current_status = self.Wifi_status
		url = "https://www.google.com/"
		timeout = 5
		try:
			request = requests.get(url, timeout=timeout)
			print("Connected to the Internet")
			self.Wifi_status = True
			if current_status != self.Wifi_status:
				self.updated_hardware_status = True
			return True
		except(requests.ConnectionError, requests.Timeout) as exception:
			print("No internet connection")
			self.Wifi_status = False
			if current_status != self.Wifi_status:
				self.updated_hardware_status = True
			return False
			
			
	def Printer_status_check_serial(self):
		current_status = self.Printer_status
		try:
			uart = serial.Serial("/dev/ttyUSB0", baudrate=19200, timeout=3000)
			self.Printer_status = True
			if current_status != self.Printer_status:
				self.updated_hardware_status = True
		except Exception as e:
			print("Exception found in ttyUSB0:", e)
			try:
				uart = serial.Serial("/dev/ttyUSB1", baudrate=19200, timeout=3000)
				self.Printer_status = True
				if current_status != self.Printer_status:
					self.updated_hardware_status = True
			except Exception as e:
				print("Exception found in ttyUSB1:", e)
				self.Printer_status = False
				if current_status != self.Printer_status:
					self.updated_hardware_status = True
				
	def refresh_hardware_status(self, screen_class):
		if self.refresh_count<= 10:
			self.refresh_count = int(self.refresh_count) + 1
			print("refresh count: ",self.refresh_count)
		else:
			try:
				screen_class.threadcondition = 1	# Turns off RFID in main sequence
				print("turned_off_rfid_temporarily...")
				time.sleep(1)
				
				print(self.multi_process_hardware_status())
				print("completed one full set of try methods for hardware status")
				self.refresh_count = 1
			except Exception as e:
				print(e)
			finally:
				screen_class.threadcondition = 0	# Turns back on RFID in main sequence
				self.refresh_count = 1
				
	def multi_process_hardware_status(self):
		try:
			Camera_process = _thread.start_new_thread(self.Camera_status_check_method,())
			Wifi_process = _thread.start_new_thread(self.internet_connection_check,())
			Thermal_Printer_Process = _thread.start_new_thread(self.Printer_status_check_serial,())
			RFID_Process = _thread.start_new_thread(self.RFID_status_check_method,())
			
			time.sleep(3)
			
			try:
				Camera_process.exit()
			except Exception as e:
				print("Exception occured in Camera status check attempting to close process due to timeout, status check already completed... Exception raised:",e)
			try:
				Wifi_process.exit()
			except Exception as e:
				print("Exception occured in WiFi status check attempting to close process due to timeout, status check already completed... Exception raised:",e)
			try:
				Thermal_Printer_Process.exit()
			except Exception as e:
				print("Exception occured in Printer status check attempting to close process due to timeout, status check already completed... Exception raised:",e)
			try:
				RFID_Process.exit()
			except Exception as e:
				print("Exception occured in RFID status check attempting to close process due to timeout, status check already completed... Exception raised:",e)
			
			return True
			
		except Exception as e:
			print(e)
			return False






if __name__ == '__main__':
	
	#Run Test Code here:
	
