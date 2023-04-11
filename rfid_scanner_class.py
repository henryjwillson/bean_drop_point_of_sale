# class to control RFID scanner
import subprocess
from subprocess import Popen, PIPE

class rfid_scanner():
	
	def __init__(self, rfid_status, scanning_status, scanning_operation):		#rfid status determines if the rfid is on (can be used to manually restart rfid program), scanning status determines if the gui is still looking to scan new cups
		self.rfid_status = rfid_status
		self.scanning_status = scanning_status
		self.scanning_operation = scanning_operation
		
	def auto_polling(self, pipe):
		# use Popen class instead of run class as Popen class returns standard output as a live feed whereas run class returns standard output only at the end of the process
		p1 = subprocess.Popen(["./rfidb1-tool /dev/ttyS0 poll"],
									cwd="/home/pi/rfidb1-tool_v1.1", shell=True, stdout= subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
		try:
			print(p1.stdout.decode())  # capure_output=True takes the response normally returned to console and returns it to the variable instead. stdout = standard output # .decode() method passes result out as a string eg. print(p1.stdout.decode())
		except Exception as error:
			print(error)
			
		while self.rfid_status == True:
			#print(self.rfid_status)
			#time.sleep(0.1)
			while self.scanning_status == True:
				try:
					value =  p1.stdout.readline()
					#print(p1.stdout.decode()) # capure_output=True takes the response normally returned to console and returns it to the variable instead. stdout = standard output # .decode() method passes result out as a string eg. print(p1.stdout.decode())
					if value[10:17] == "NTAG213":
						rfid_size = p1.stdout.readline()
						rfid_uid = p1.stdout.readline()
						formatted_rfid_uid = rfid_uid[5:20]
						pipe.send(formatted_rfid_uid)
				except Exception as error:
					print(error)
					pass
					

# File Testing
if __name__ == '__main__':
	
	import subprocess
	from subprocess import Popen, PIPE
	import time
	from multiprocessing import Process, Pipe
	import sys
	
	(ParentEnd, ChildEnd) = Pipe()
	cup_scanner = rfid_scanner(True, True, "ADD")
	child = Process(target = cup_scanner.auto_polling, args=(ChildEnd,))
	child.start()
	
	Scanned_list = []
	
	while True:
		last_scanned_rfid = ParentEnd.recv()
		print("parent end recieved....", last_scanned_rfid)
		
		if last_scanned_rfid in Scanned_list:
			print("rfid already in list")
		else:
			Scanned_list.append(last_scanned_rfid)
			print("current scanned list",Scanned_list)
		pass

