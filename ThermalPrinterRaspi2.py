# On the Raspberry Pi with the USB-to-serial converter:
from Screen_Numbers_Class import *
import serial
import qrcode
from Adafruit_Thermal import * #Importing Galactics fans adafruit thermal printer conversion for image printing
import MediumLogoBitMap as MediumBean
import adafruit_thermal_printer


class bean_drop_thermal_printer_class:
	
	def __init__(self, location, baud_rate, time_out, printer_class):
		self.location = location
		self.baud_rate = baud_rate
		self.time_out = time_out
		self.printer_class = printer_class
		
	def print_customer_reciept(self, order_class, order_date_time):
		try:
			uart = serial.Serial("/dev/ttyUSB0", baudrate=19200, timeout=3000)
		except Exception as e:
			print("Exception captured with thermal printer during serial connection is: ", e)
		else:
			ThermalPrinter = adafruit_thermal_printer.get_printer_class(self.printer_class)
			printer = ThermalPrinter(uart, auto_warm_up=False)
			printerI = Adafruit_Thermal("/dev/ttyUSB0", 19200, timeout=5)
			
			print_user_number = str(order_class.user_account_number)[0:40]
			print_order_number = str(order_class.local_order_id)
			print_cups_ordered = "Cups on order: " + str(order_class.amount_of_RFID_Numbers_Registered)
			print_current_date_time = order_date_time
			print_pos_hash = str(order_class.POS_hash)[0:40]
			print_cups_ordered = str(order_class.amount_of_RFID_Numbers_Registered)
			printerI.setTimes(500, 500) #500 (SMALLEST NUMBER WITHOUT ERRORS), 500 working
			#printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
			printerI.set_dtr_pin(2)
			printerI.justify('C')
			printerI.printBitmap(MediumBean.width, MediumBean.height, MediumBean.MediumLogoBitMap)
			printerI.println("Welcome to Bean Drop")
			printerI.feed(1)
			printerI.println("Your new customer details")
			printerI.feed(1)
			printerI.println("Customer Account Number")
			printerI.println(print_user_number)
			printerI.println("Local order number")
			printerI.println(print_order_number)
			printerI.println("Sign up code")
			printerI.println(print_pos_hash)
			printerI.println("Cups Ordered")
			printerI.println(print_cups_ordered)
			printerI.feed(2)
			printerI.println("Keep these details extra safe, you'll need these to register later. To register download the Bean Drop app or go to http://beandrop.net/register")
			printerI.println(print_current_date_time)
			printerI.feed(2)
			
			self.make_qr_code(print_user_number)
			printerI.printImage("some_file.png")
			#printerI.printImage("some_file.png", LaaT=True)
			#self.print_customer_qr_code()
			
			printer.feed(2)
			
	def print_customer_qr_code(self):
		printerI = Adafruit_Thermal("/dev/ttyUSB0", 19200, timeout=5)
		printerI.setTimes(5000, 1000)
		printerI.printImage("some_file.png", LaaT=True)
		
	def make_qr_code(self,new_customer_qr_code):
		#img = qrcode.make('jhsdgkfjhagkflhwgkdfjhbqwf')
		img = qrcode.make(new_customer_qr_code)
		type(img)  # qrcode.image.pil.PilImage
		img.save("some_file.png")
		
	def print_totals(self, totals_name, totals_class, start_date, end_date):
		try:
			uart = serial.Serial("/dev/ttyUSB0", baudrate=19200, timeout=3000)
		except Exception as e:
			print("Exception captured with thermal printer during serial connection is: ", e)
		else:
			ThermalPrinter = adafruit_thermal_printer.get_printer_class(self.printer_class)
			printer = ThermalPrinter(uart, auto_warm_up=False)
			printer.print("Bean Drop Cups Sales Totals")
			printer.feed(2)
			printer.print("Start date:")
			printer.print(start_date)
			printer.print("End date:")
			printer.print(end_date)
			printer.feed(2)
			cup_total_str = str("Total cups: " + str(totals_class.cup_total))
			printer.print(cup_total_str)
			deposit_total_str = str("Cup deposits: " + str(totals_class.deposit_total))
			printer.print(deposit_total_str)
			deposit_value_str = str("Deposit value: " + str(totals_class.deposit_value) + "GBP")
			printer.print(deposit_value_str)
			
			printer.feed(4)
		
			
			
if __name__ == '__main__':
	# Internal Testing

	print("This is running ThermalPrinterRaspi2 as '__main__'")

	# ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.168)
	# #ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)

	try:
		uart = serial.Serial("/dev/ttyUSB0", baudrate=19200, timeout=3000)
	except Exception as e:
		print("Exception captured with thermal printer during serial connection is: ", e)
	#uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=3000)
	
	
	mainscreen_class_test = screen_numbers(0, False, "henry willson", 0, 0, "", 0, 0, 0, 3, 1, 0, 0, 0,"", "", "", "", "", False)
	Test_thermal = bean_drop_thermal_printer_class("/dev/ttyUSB0", 19200, 5, 2.168)
	customer_string = "k;aslgjhflskadfgghjbcasdcvawv"
	Test_thermal.make_qr_code(customer_string)
