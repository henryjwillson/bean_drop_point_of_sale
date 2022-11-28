from tkinter import *
import time
import math
import multiprocessing
from multiprocessing import Process, Pipe
import RPi.GPIO as GPIO
from PIL import Image, ImageTk
import subprocess
import os                                   # used for various directory commands, used in conjuction with omx music player
import traceback                            # used to traceback errors when diagnosing terminal output

from Bean_drop_sales_values import Bean_drop_sales_values   #Class used to hold values of the various Bean Drop charges
BD_charge = Bean_drop_sales_values(3.00, 0.25, 0.25, 0.25)


import _thread
import queue
import sqlite3								# Used as local database for access to orders without need for connection to server network
import datetime								# Time tracking
from datetime import timedelta
# Used for dictionary temporary memory tracking. (using collections.abc because collections is being phased out...)
from collections.abc import Mapping
import mysql.connector
from mysql.connector import errorcode
from QR_Code_Internet_Example_For_POSGUI import POS_QR_Reader, QR_Check_user_account, camera_qr_scanner #Importing Camera / QR Code reader #Importing new camera_qr_scanner class
import csv
from ThermalPrinterRaspi2 import *
from rfid_scanner_class import rfid_scanner #importing new always on rfid scanner class

from Screen_Numbers_Class import screen_numbers
from cafe_totals_class import *
from Check_user_account_addition import check_user_account_addition2, insert_order_new_user_bluehost2
from Frame_Sizing_Class import Frame_Sizing
from Hardware_status import *

from POS_local_db_class import POS_local_db_class, offset_numbers_class, offset_order_class, update_cups_in_old_order_dict2 #,update_cups_in_old_order_dict
print("POS_local_db_class imported")

from Connect_functions import server_connection_details
from certs.program_connection_details import * #importing the local connection details file
from Cafe_details.passlib_authentication_module import hash_pwd, verify_pwd, combined_variables_hash
from Cafe_details.Cafe_class import Cafe_class

import smbus
import sys
bus = smbus.SMBus(1)
address = 0x08          # Arduino I2C Address

GPIO.setmode(GPIO.BCM)

# Set pin 7 to be input pin and set initial value to be pulled low (off)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(26, GPIO.OUT)  # Pin 26 sends signal to confirm safe shutdown

GPIO.setup(5, GPIO.OUT) #Turns Arduino on
GPIO.output(5, GPIO.HIGH)


# Setting up Sound Output-------------------------------------------------------------------
cwd_retrieve = os.getcwd()      # Command to retrieve current working directory of this python program
music_directory = str(cwd_retrieve) + "/GUI_Sounds" #Appends string to GUI_Sounds directory
#------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Current Date Time
def datetime_formatted():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def shutdown(pid):
    # os.kill(pid, signal.SIGSTOP)
    # os._exit(1)
    command = "/usr/bin/sudo /sbin/shutdown -h now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)


def reset_button(time_of_reset, pid):
    while True:  # Run forever
        buttonstate = GPIO.input(6)
        if buttonstate == False:
            print(time_of_reset)
            time.sleep(1)
            shutdown(pid)
            break

pid = os.getpid()
rb1 = Process(target=reset_button, args=(datetime_formatted,pid))		# args here a Tuple...
rb1.start()

# Initialising Screen Numbers Class
mainscreen = screen_numbers(0, False, "henry willson", 0, 0, "", 0, 0, 0, 0, 0, 0, 0, 0,"", "", "", "", "", False)
screen_choice_class = mainscreen

#server_connection_details class--------------------------------------------------------------------------------------------------
#server1 = server_connection_details('162.241.252.101','3306', "beandrop_RaspiPiDemo", "bluehostdemo1!", 'beandrop_WPIED')
server1 = server_connection_details(local_con_details.host, local_con_details.port, local_con_details.user, local_con_details.pwd, local_con_details.DB_Name, local_con_details.ssl_ca, local_con_details.ssl_cert, local_con_details.ssl_key)

# Populating temporary list of cafe accounts which are restricted and cannot be used to make an order.
try:
    cafe_list = server1.admin_recall_cafe_dictionary()
    cafe_list_length = len(cafe_list)
    cafe_dictionary = {}
    for k in range (1, cafe_list_length + 1):       #Converting list to dictionary as it will be faster to sort through in future compared to that of a list
            cafe_dictionary[k] = str(cafe_list[k-1])[2:42]
    print("printing the cafe dictionary: ",cafe_dictionary)
except Exception as cafe_dictionary_error:
    print("cafe_dictionary{} error is : ",cafe_dictionary_error)

#local database class-----------------------------------------------------------------------------------------------------------
local_db = POS_local_db_class("new_method_local_db2.db")


#----------------------------------------------------------------------------------
#Selecting Frame Sizing Class
main_frame_size = Frame_Sizing(1024,600)

#----------------------------------------------------------------------------------
# main_hardware updating status check on launch
main_hardware.refresh_hardware_status(mainscreen)

def hardware_status_update_timer():
    while True:
        time.sleep(3)
        main_hardware.refresh_hardware_status(mainscreen)
        
#----------------------------------------------------------------------------------

def number_add():
    global number_count  # variable must be made global for class reference
    number_count = number_count + 1
    print(number_count)


def register_cup():
    mainscreen.amount_of_RFID_Numbers_Registered = mainscreen.amount_of_RFID_Numbers_Registered + 1


def register_cup_removal():
    mainscreen.amount_of_RFID_Numbers_Registered = mainscreen.amount_of_RFID_Numbers_Registered - 1


global screen_change_check
screen_change_check = 0

number_count = 1

# Image Processing --------------------------------------------------------------------------------------------------------------------------------------------
# Images must be instigated in tk after tk opened later on
# Beandrop Logo Icon
beandrop_logo = Image.open("/home/pi/Pictures/homelogo.png")
# print(beandrop_logo.size)
beandrop_logo_new_crop = beandrop_logo.crop((260, 100, 540, 380))       #beandrop_logo_new_crop = beandrop_logo.crop((210, 50, 590, 430)) Old logo size was a little bit too small
# beandrop_logo_new_crop.show()
beandrop_logo_new_height = 100
# integer required for resize, not a float (float is a number with decimals)
beandrop_logo_new_width = int(beandrop_logo_new_height /
                              beandrop_logo_new_crop.height * beandrop_logo_new_crop.width)
beandrop_logo_new_size = beandrop_logo_new_crop.resize(
    (beandrop_logo_new_width, beandrop_logo_new_height))
beandrop_logo_new_size.show()

# Coffee Icon
coffee_icon = Image.open("/home/pi/Pictures/coffee_icon.png")
# print(coffee_icon.size)
coffee_icon_new_height = 70
# integer required for resize, not a float (float is a number with decimals)
coffee_icon_new_width = int(coffee_icon_new_height / coffee_icon.height * coffee_icon.width)
coffee_icon_new_size = coffee_icon.resize((coffee_icon_new_width, coffee_icon_new_height))
# coffee_icon_new_size.show()
print(coffee_icon_new_size.size)
coffee_icon_new_crop = coffee_icon_new_size.crop((5, 0, 65, 70))
print(coffee_icon_new_crop.size)
coffee_icon_new_crop.show()

# Coffee Bean Icon
coffee_bean_icon = Image.open("/home/pi/Pictures/coffee_bean_icon.png")
# print(coffee_bean_icon.size)
coffee_bean_icon_new_height = 70
# integer required for resize, not a float (float is a number with decimals)
coffee_bean_icon_new_width = int(coffee_bean_icon_new_height /
                                 coffee_bean_icon.height * coffee_bean_icon.width)
coffee_bean_icon_new_size = coffee_bean_icon.resize(
    (coffee_bean_icon_new_width, coffee_bean_icon_new_height))
# coffee_bean_icon_new_size.show()
print(coffee_bean_icon_new_size.size)


# Python3 code to demonstrate working of
# Get total keys in dictionary
# Utility function to perform task
def total_keys(test_dict):
    for key, value in test_dict.items():
        if isinstance(value, Mapping):
            yield from total_keys(value)
    yield len(test_dict)


# Initialize dictionary
global cups_used_dictionary
cups_used_dictionary = {}
global cups_used_numbers
# This is a counter for the dictionary, not for number of cups in the order. Maybe higher than in order as cups are removed. (adding cups up later needs looking when keys are deleted / skipped)
cups_used_numbers = 1

# Using yield() + recursion
# Get total keys in dictionary
res = sum(total_keys(cups_used_dictionary))

# Getting Key Value to Modify / Remove Tag from order which is in local dictionary
def get_key(val):
    for key, value in cups_used_dictionary.items():
        if val == value:
            return key

#-------------------------------------------------------------------------
# Secondary dictionary used for temporary populating when looking back through previous order history. Used to populate with RFID numbers
global cups_in_old_order_dictionary
global number_of_cups_in_old_order
number_of_cups_in_old_order = 1
cups_in_old_order_dictionary = {}

# Refund dictionary; this is used to when scanning in cups for a refund, this dictionary is compared to secondary dictionary for additions.
global cups_found_in_refund_dictionary
global number_of_cups_found_in_refund #Variable is used to display number of cups added to refund order
number_of_cups_found_in_refund = 1
cups_found_in_refund_dictionary = {}

# Third dictionary used in refunds as temporary storage when checking for partial refunds
global updated_cups_in_old_order_dictionary
global number_of_cups_in_update_dictionary
number_of_cups_in_update_dictionary = 1
updated_cups_in_old_order_dictionary = {}


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Print Errors Out Method

def Error_Print_Method_mySQL(error):
    print("Error code:", error.errno)        # error number
    print("SQLSTATE value:", error.sqlstate) # SQLSTATE value
    print("Error message:", error.msg)       # error message
    print("Error:", error)                   # errno, sqlstate, msg values
    s = str(error)
    print("Error:", s)                   # errno, sqlstate, msg values

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#SQLite3 Database for local admin users
class local_admin_db_actions():
    
    def __init__(self, db_name, super_user, super_user_pwd):
        self.db_name = db_name
        self.super_user = super_user
        self.super_user_pwd = super_user_pwd
        
        
    def create_local_admin_user_db(self):
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""CREATE TABLE local_admin_users (
                        user_name varchar(20),
                        user_pin varchar(8),
                        UNIQUE (user_name)
                        )""")
                print("New admin table successfully built")
                return True
        except sqlite3.Error as err:
            print("The error in creating admin user_table was", err)
            return False
            
    def add_new_admin_user(self, user_name, pwd):
        hashed_pin = hash_pwd(pwd)
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""INSERT into local_admin_users VALUES (
                        :user_name,
                        :user_pin)""", {'user_name': user_name, 'user_pin': hashed_pin})
                print("New admin user succesfully added")
                return True
        except sqlite3.Error as err:
            print("The error in creating new_admin_user was", err)
            return False
        
    def check_admin_user_name_free(self, user_name):
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""SELECT user_name FROM local_admin_users""")
                user_name_list = c.fetchall()
                if user_name in user_name_list:
                    print("User name is currently already in use")
                    return False
                else:
                    print("user name is free to use")
                    return True
                print("New admin user inserted into table")
        except sqlite3.Error as err:
            print("The error in creating new_admin_user was", err)
        
    def verify_user(self, user_name, pwd):
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""SELECT user_pin FROM local_admin_users WHERE user_name = ?""", (user_name,))
                returned_pwd = c.fetchone()[0]
                if verify_pwd(pwd, returned_pwd) == True:
                    print("correct pin code for admin user found")
                    return True
                else:
                    print("incorrect admin user pin entered")
                    return False
        except sqlite3.Error as err:
            print("SQL error during admin pin verifications was:", err)
            
    def change_admin_pwd(self, user_name, new_pwd):
        hashed_pin = hash_pwd(new_pwd)
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""UPDATE local_admin_users SET user_pin = ? WHERE user_name = ?;""", (hashed_pin, user_name))
                print("admin pin updated in local db")
                return True
        except sqlite3.Error as err:
            print("SQL error during admin pin updating was:", err)
            return False
            
    def return_user_list(self):
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""SELECT user_name FROM local_admin_users""")
                user_name_list = c.fetchall()
                formatted_list = []
                for item in user_name_list:
                    formatted_list.append(item[0])
                return formatted_list
        except sqlite3.Error as err:
            print("The error in selecting returning users names from admin user database was:", err)
            
    def super_admin_remove_user(self, user_name):
        conn_local_db = sqlite3.connect(self.db_name)
        c = conn_local_db.cursor()
        try:
            with conn_local_db:
                c.execute("""DELETE FROM local_admin_users WHERE user_name = ?;""", (user_name,))
                print("admin user removed from local db")
                return True
        except sqlite3.Error as err:
            print("SQL error during admin removal from db was:", err)
            return False
    
# Initiating the admin database class        
local_admin_user = local_admin_db_actions(local_con_details.admin_user_db, local_con_details.super_admin, local_con_details.super_admin_pin)
new_admin_user_database = local_admin_user.create_local_admin_user_db()
if new_admin_user_database:     #if database does not exist, generate super admin user
    local_admin_user.add_new_admin_user(local_con_details.super_admin, local_con_details.super_admin_pin)
    temp_user_list = local_admin_user.return_user_list()
    print("temp user admin list is:", temp_user_list)

local_admin_user.add_new_admin_user("Temp_test_user", "1234")
temp_user_list = local_admin_user.return_user_list()
print("temp user admin list is:", temp_user_list)
# SQLite3 Database connection for local backups-------------------------------------------------------------------------------------------------------------------------------------------------

# List conversion function
def convert_list_to_string(org_list, seperator=' '):
    """ Convert list to string, by joining all item in list with given separator.
        Returns the concatenated string """
    return seperator.join(org_list)

# Initialising Offset classes -------------------------------------------------------------------------------------------------------------
main_offset_class = offset_numbers_class(0, 1, 2, 3, 4, 0) #Creates the offset_number_class imported from POS_local_db_class 
first_offset_order_class = offset_order_class(0,0,0,0,0,0,0,0)    #Generating the first offset_order_class
second_offset_order_class = offset_order_class(0,0,0,0,0,0,0,0)   #Generating the second offset_order_class
third_offset_order_class = offset_order_class(0,0,0,0,0,0,0,0)    #Generating the third offset_order_class
fourth_offset_order_class = offset_order_class(0,0,0,0,0,0,0,0)   #Generating the fourth offset_order_class
fith_offset_order_class = offset_order_class(0,0,0,0,0,0,0,0)     #Generating the fith offset_order_class
selected_offset_order_class = offset_order_class(0,0,0,0,0,0,0,0) #Generating the selected offset_order_class which is used at the individual order screen


def check_last_order_offset(offset):
    # Hidden function due to commericial sensitivity


def check_last_order_offset_order_id_overall_local(offset):
    # Hidden function due to commericial sensitivity


def check_last_order_offset_order_datetime(offset):
    # Hidden function due to commericial sensitivity


def check_last_order_offset_cups_registered_local(offset):
    # Hidden function due to commericial sensitivity


def check_last_order_offset_order_value_local(offset):
    # Hidden function due to commericial sensitivity
    
def check_user_unique_ID_local(offset):
    # Hidden function due to commericial sensitivity


# queue.Queue() Setup-------------------------------------------------------------------------------------------------------------------------------------------
dataQueue = queue.Queue()															# Shared global storage queue, infinite size


# Launching QR camera class ----------------------------------------------------------------------------------------------------------
POS_QR_Scanner = camera_qr_scanner(True, False, True)
(QR_multiprocess_parent, QR_multiprocess_child) = Pipe()
_thread.start_new_thread(POS_QR_Scanner.start_camera_data_recording,(QR_multiprocess_parent, mainscreen, server1, cafe_dictionary, dataQueue))

# RFID's Sold in last 2 hours list ---------------------------------------------------------------------------------------------
recent_local_rfid_scans_list = []

def update_recent_local_rfids_in_orders_list(start_message):
    print(start_message)
    while True:
        global recent_local_rfid_scans_list
        historic_time = (datetime.datetime.now() - timedelta(hours = 1))
        #print(time_now, historic_time)
        historic_order_list = local_db.return_historic_orders_in_time_period()
        recent_local_rfid_scans_list.clear()
        #print("historic_order_list is: ", historic_order_list)
        for order in historic_order_list:
            if datetime.datetime.strptime(order[1],'%Y-%m-%d %H:%M:%S') >= historic_time:
               recent_local_rfid_scans_list.append(order[0]) 
        print("recent_local_rfid_scans_list is: ", recent_local_rfid_scans_list)
        time.sleep(5)       

_thread.start_new_thread(update_recent_local_rfids_in_orders_list,("start_message",))

# RFID Polling Method ----------------------------------------------------------------------------------------------------------------
# Initialising RFID Scanner Class
cup_scanner = rfid_scanner(True, True, "ADD")
(ParentEnd, ChildEnd) = Pipe()
child = Process(target = cup_scanner.auto_polling, args=(ChildEnd,))
child.start()

def rfid_scanner_add():
    cup_scanner.scanning_status = True
    cup_scanner.scanning_operation = "ADD"

def rfid_scanner_remove():
    cup_scanner.scanning_status = True
    cup_scanner.scanning_operation = "REMOVE"

def rfid_scanner_off():
    cup_scanner.scanning_status = False
    cup_scanner.scanning_operation = "REMOVE"
    
def rfid_dictionary_updater():    
    global cups_used_numbers
    global recent_local_rfid_scans_list
    print("--INFO--: STARTING RFID LISTENER PROGRAM")
    
    while True:
        
        if cup_scanner.scanning_status == True:
            last_scanned_rfid = ParentEnd.recv()
            if cup_scanner.scanning_operation == "ADD":
                print("starting rfid_checker loop")
                print("just recieved a scanned rfid from child process: ",last_scanned_rfid)
                already_registered = last_scanned_rfid[:-1] in cups_used_dictionary.values()
                if already_registered == False:  # If statement stops duplicate adding of cup RFID's in a single order by registering a list in a dictionary
                    print("-- INFO -- : This is the recent_local_rfid_scans_list: ", recent_local_rfid_scans_list)
                    if last_scanned_rfid[:-1] in recent_local_rfid_scans_list:
                        print("WARNING THIS RFID HAS ALREADY BEEN USED IN AN ORDER IN THE LAST HOUR")
                        mainscreen.cup_recently_scanned_warning = True
                        mainscreen.variable_text_output = last_scanned_rfid[:-1]
                        p3 = subprocess.run(["omxplayer --no-keys -o both ErrorNotification.mp3 &"], cwd = '/home/pi/Documents/cloned_repo/mu_code/GUI/POS GUI/POS1_8T/GUI_Sounds', shell=True)
                        dataQueue.put(last_scanned_rfid)
                    else:
                        mainscreen.cup_recently_scanned_warning = False
                        mainscreen.variable_text_output = ""
                        cups_used_dictionary[cups_used_numbers] = last_scanned_rfid[:-1]
                        cups_used_numbers = cups_used_numbers+1
                        print(cups_used_dictionary)
                        p3 = subprocess.run(["omxplayer --no-keys -o both CheckoutScan.wav &"], cwd = '/home/pi/Music', shell=True)
                        register_cup()
                        dataQueue.put(last_scanned_rfid)
                else:
                    print("cup already registered")
                    print(cups_used_dictionary)
            elif cup_scanner.scanning_operation == "REMOVE":
                already_registered = last_scanned_rfid in cups_used_dictionary.values()
                if already_registered == True:  # If statement stops duplicate adding of cup RFID's in a single order by registering a list in a dictionary
                    print(get_key(last_scanned_rfid))
                    del cups_used_dictionary[get_key(last_scanned_rfid)]
                    print("Removed Key from dictionary, new updated dictionary", cups_used_dictionary)
                    print(cups_used_dictionary)
                    p3 = subprocess.run(["omxplayer --no-keys -o both CheckoutScan.wav &"], cwd = '/home/pi/Music', shell=True)
                    register_cup_removal()
                    dataQueue.put(last_scanned_rfid)
                    time.sleep(0.5)
                else:
                    # No warning of cup not being already registered on screen yet....
                    print("cup is not yet registered, can't remove cup")
                    print(cups_used_dictionary)
                    # Not adding data, but adds to queue which is being checked, a value in the queue causes screen update
                    dataQueue.put(last_scanned_rfid)
                    # Added time after removing cup prevents adding of cup immediately after
                    time.sleep(0.25)


def POS_QR_Reader_Run(screen_numbers, cafe_class):
    screen_numbers.threadcondition == 1
    QR_Runner = POS_QR_Reader(screen_numbers, cafe_class, cafe_dictionary)
    print("QR_Runner result (True or Flase) is : ",QR_Runner)
    if QR_Runner == True:
        dataQueue.put("Complete")
        print("QR Code complete")
        with open('barcodes.csv', newline = '') as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)
    print("QR Code method complete")


class AppFrame(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent, width=main_frame_size.width, height=main_frame_size.height, bg="light blue")
        self.bind("<0xff8d>", self.OnReturn)
        # Binds number 4 to the Options frame event
        self.bind("<0xffb4>", self.options_frame_event)
        # Binds number 1 to old orders frame event
        self.bind("<0xffb1>", self.old_orders_frame_event)
        # Binds number 2 to the Remove Cup frame event
        self.bind("<0xffb2>", self.remove_cup_frame_event)
        self.bind("<0xffb5>", self.paid_frame_event)								# Binds number 5 to the PAID frame event
        # Simple root.quit() event to cancel mainloop() and end program
        self.bind("<BackSpace>", self.Quit_Event)
        # Binds plus to Adding a customer method
        self.bind("<0xffab>", self.add_customer_event)
        # Binds slash to Reseting an order method
        self.bind("<0xffaf>", self.Reset_Order_Event)
        # only works when program is not in fullscreen, focus_force() only works in fullscreen
        self.focus_set()
        # self.focus_force() 														# must set focus to Frame for button binds to work
        self.grid_location(0, 0) 													# setting frame starting location in root window
        # setting row sizes my runnning repeat row configures, rows and columns in .grid start at value of zero (0).
        for r in range(0, 8):
            self.grid_rowconfigure(r, minsize=main_frame_size.row_size_8)
        for c in range(0, 10):
            self.grid_columnconfigure(c, minsize=main_frame_size.column_size_10)
        # self.grid_rowconfigure(0,minsize=50)
        # self.grid_columnconfigure(0, minsize=80)
        # self.grid_columnconfigure(1, minsize=160)
        self.grid(sticky=W+E+N+S)													# Sticky W+E+N+S causes grid to expand to frame size
        self.make_widgets()
        self.app_frame_central_screen()
        self.make_customer()
        self.hardware_warning_symbols()
        print("--INFO-- \nSTARTING POLLING THREAD")
        self.Polling_test()
        #self.flat_bean_drop_logo()
        # Set at 250 which is the same as the polling rate [Don't remove, stops updating...] Everytime there is a success, updates continue to add on...
        self.after(250, lambda: self.Update_Frame())

    def make_widgets(self):
        Old_Orders_Label = Button(self, text="OLD ORDERS [1]", bg="orange", relief=RAISED, command = self.old_orders_frame_event2)
        Old_Orders_Label.grid(column=0, columnspan=2, row=0, sticky=W+E+N+S)
        #Big_Number_Label = Label(self, text=mainscreen.amount_of_RFID_Numbers_Registered, bg="light blue", font="Helvetica -200")
        #Big_Number_Label.grid(column=2, columnspan=6, row=1, rowspan=5, sticky=W+E+N+S)
        Remove_Label = Button(self, text="REMOVE CUP [2]", bg="yellow", relief=RAISED, command = self.remove_cup_frame_event2)
        Remove_Label.grid(column=8, columnspan=2, row=2, sticky=W+E+N+S)
        Reset_Label = Button(self, text="RESET [/]", bg="red", relief=RAISED, command = self.Reset_Order_Event2)
        Reset_Label.grid(column=8, columnspan=2, row=3, sticky=W+E+N+S)
        Paid_Label = Button(self, text="PAID [5]", bg="#75FF00", relief=RAISED, command = self.paid_frame_event2)
        Paid_Label.grid(column=8, columnspan=2, row=5, sticky=W+E+N+S)
        Options_Label = Button(self, text="OPTIONS [4]", bg="#DA63FF", relief=RAISED, command = self.options_frame_event2)
        Options_Label.grid(column=0, columnspan=2, row=5, sticky=W+E+N+S)
        beandrop_logo_image_label = Label(
            self, image=beandrop_logo_new_size, bg="white", relief=RAISED)
        beandrop_logo_image_label.grid(column=8, columnspan=2, row=0, rowspan=2, sticky=W+E+N+S)

        # bottom frame widget for containing payment numbers
        bottom_frame = Frame(self, width=main_frame_size.width, height=main_frame_size.row_size_8*2, bg="white", bd=10, relief=RAISED)
        bottom_frame.grid(column=0, columnspan=10, row=6, rowspan=2, sticky=W+E+N+S)
        for c in range(0, 10):
            bottom_frame.grid_columnconfigure(c, minsize=main_frame_size.column_size_10-2)
        bottom_frame.grid_rowconfigure(0, minsize=main_frame_size.row_size_8*1.6) #Was 80 when the value of total height was 100

        cup_count_number_label = Label(
            bottom_frame, text=mainscreen.RFIDCups_minus_account_cups, bg="white", font="Helvetica -40", fg="blue")
        cup_count_number_label.grid(column=2, row=0, sticky=W+E+N+S)
        first_multiply_label = Label(bottom_frame, text="x", bg="white", font="Helvetica -40")
        first_multiply_label.grid(column=3, row=0, sticky=W+E+N+S)
        cup_count_image_label = Label(bottom_frame, image=coffee_icon_new_crop, bg="white")
        cup_count_image_label.grid(column=4, row=0, sticky=W+E+N+S)
        equals_label = Label(bottom_frame, text="=", bg="white", font="Helvetica -40")
        equals_label.grid(column=5, row=0, sticky=W+E+N+S)
        # passing in the selected screenchoice which represents a screen_numbers class choice...
        cost_label = Label(bottom_frame, text=("£", format(mainscreen.Beandrop_payment_value,'.2f')),
                           bg="white", fg="red", font="Helvetica -40")
        cost_label.grid(column=6, columnspan=2, row=0, sticky=W+E+N+S)
        
    def app_frame_central_screen(self):
        '''This method is used to construct the central section of the AppFrame, switching between the main number label for number of cups scanned
        and various warnings (cup used in order recently...)'''
        if mainscreen.cup_recently_scanned_warning == False:
            try:
                for widget in (self.recent_cup_warning_message, self.yes_accept_cup_button, self.cancel_cup_button):
                    widget.grid_forget()
            except Exception as e:
                print(e)
            self.Big_Number_Label = Label(self, text=mainscreen.amount_of_RFID_Numbers_Registered, bg="light blue", font="Helvetica -200")
            self.Big_Number_Label.grid(column=2, columnspan=6, row=1, rowspan=5, sticky=W+E+N+S)
        elif mainscreen.cup_recently_scanned_warning == True:
            try:
                for widget in (self.Big_Number_Label):
                    widget.grid_forget()
            except Exception as e:
                print(e)
            self.recent_cup_warning_message = Label(self, text="-- WARNING --\nThe last cup you scanned was recently sold in another order. \ndo you still want to add the cup to this order?", bg="light blue", font="Helvetica -35", fg="red", wraplength=(main_frame_size.column_size_10*6)-30)
            self.recent_cup_warning_message.grid(column=2, columnspan=6, row=1, rowspan=3, sticky=W+E+N+S)
            self.yes_accept_cup_button = Button(self, text="ADD TO ORDER", bg="light green", relief=RAISED, command = lambda: self.add_warning_recent_cup_to_order())
            self.yes_accept_cup_button.grid(column=5, columnspan=2, row=4, rowspan=1, sticky=W+E+N+S, padx = 10, pady = 10)
            self.cancel_cup_button = Button(self, text="CANCEL", bg="red", relief=RAISED, command = lambda: self.cancel_warning_recent_cup_to_order())
            self.cancel_cup_button.grid(column=3, columnspan=2, row=4, rowspan=1, sticky=W+E+N+S, padx = 10, pady = 10)
                
    def add_warning_recent_cup_to_order(self):
        global cups_used_numbers
        global recent_local_rfid_scans_list
        mainscreen.cup_recently_scanned_warning = False
        cups_used_dictionary[cups_used_numbers] = mainscreen.variable_text_output
        cups_used_numbers = cups_used_numbers+1
        print(cups_used_dictionary)
        p3 = subprocess.run(["omxplayer --no-keys -o both CheckoutScan.wav &"], cwd = '/home/pi/Music', shell=True)
        register_cup()
        dataQueue.put(mainscreen.variable_text_output)
    
    def cancel_warning_recent_cup_to_order(self):
        mainscreen.cup_recently_scanned_warning = False
        dataQueue.put(mainscreen.variable_text_output)
            

    def make_customer(self):
        if mainscreen.user_account_number == 0:
            add_customer_label = Button(self, text=("ADD CUSTOMER [+]"), bg="#33BCFF", relief=RAISED, command = self.add_customer_event2)
            add_customer_label.grid(column=2, columnspan=6, row=0, sticky=W+E+N+S)
        else:
            test_label = Button(self, text=(mainscreen.username, "Deposits in account: ",
            mainscreen.cups_in_user_account), bg="#75FF00", relief=RAISED, command = self.add_customer_event2)
            test_label.grid(column=2, columnspan=6, row=0, sticky=W+E+N+S)
        # button_test = Button(self, text="switch to class 2", command = (lambda: self.Launch_SecondFrame()))				# Old manual click buttons on screen, left as comments for future reference
        # button_test.grid(column=0, columnspan=2, row=2, rowspan=2, sticky=W+E+N+S)
        
    def flat_bean_drop_logo(self):
        beandrop_logo_image_label = Label(
            self, image=beandrop_logo_new_size, bg="white", relief=FLAT)
        beandrop_logo_image_label.grid(column=8, columnspan=2, row=0, rowspan=2, sticky=W+E+N+S)
        
    def back_button_generic(self):
        back_label = Button(self, text="Back [/]", bg="yellow", relief=RAISED, bd=5, command = self.back_button_generic_action)
        back_label.grid(column=0, columnspan=2, row=0, sticky=W+E+N+S)
    
    def back_button_generic_action(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        mainscreen.entry_widget_user_number = ""
        self.destroy()
        mainscreen.back_button_press_screen(root)
        
    def hardware_warning_symbols(self):
        if main_hardware.RFID_status == False:
            RFID_status_red_label = Label(self, text="RFID ERROR", bg="light blue", fg="red", font="Helvetica -20", wraplength=100)
            RFID_status_red_label.grid(column=0, columnspan=1, row=1, sticky=W+E+N+S)
        else:
            pass
        if main_hardware.Wifi_status == False:
            Wifi_status_red_label = Label (self, text="WIFI ERROR", bg="light blue", fg="red", font="Helvetica -20", wraplength=100)
            Wifi_status_red_label.grid(column=0, columnspan=1, row=2, sticky=W+E+N+S)
        else:
            pass
        if main_hardware.Camera_status == False:
            Camera_status_red_label = Label(self, text="CAMERA ERROR", bg="light blue", fg="red", font="Helvetica -20", wraplength=100)
            Camera_status_red_label.grid(column=0, columnspan=1, row=3, sticky=W+E+N+S)
        else:
            pass
        if main_hardware.Printer_status == False:
            Printer_status_red_label = Label(self, text="PRINTER ERROR", bg="light blue", fg="red", font="Helvetica -20", wraplength=100)
            Printer_status_red_label.grid(column=0, columnspan=1, row=4, sticky=W+E+N+S)
        else:
            pass
            
    def numpad_admin_list(self):
        #Drop down menu variables
        self.local_admin_user_list = local_admin_user.return_user_list()
        self.admin_user_option_var = StringVar()
        self.admin_user_option_var.set(self.local_admin_user_list[0])  # setting the initial entry value to nothing
        mainscreen.selected_admin_user = self.admin_user_option_var.get()
        
    def make_numpad(self):
        global Entry_white_box
        # Variable which is linked to entry widget
        self.var = StringVar()  # linked entry value to customer entry widget, linked to .get() function
        self.var.set(mainscreen.entry_widget_user_number)  # setting the initial entry value to nothing
        
        
        Num_pad_frame = Frame(self, width=main_frame_size.column_size_10*4, height=main_frame_size.row_size_8*6, bg="#86d0d0", relief = RAISED, bd=5)
        Num_pad_frame.grid(column=2, columnspan=5, row=0, rowspan=8, sticky=W+E+N+S, padx=main_frame_size.column_size_10/2, pady=10)
        for r2 in range(0, 6):
            Num_pad_frame.grid_rowconfigure(r2, minsize=main_frame_size.row_size_8*1.25-2)
        for c2 in range(0, 3):
            Num_pad_frame.grid_columnconfigure(c2, minsize=main_frame_size.column_size_10*1.3-2)
            
        Entry_white_box = Entry(Num_pad_frame, bg="white", bd=5, font="Helvitica -18 bold", justify=CENTER, show="*")
        Entry_white_box.grid(column=0, columnspan=3, row=1, rowspan=1, sticky=W+E+N+S, padx=10, pady=20)
        Entry_white_box.config(textvariable=self.var)
        Entry_white_box.focus_set()
        
        
        Bean_drop_station_selection_option_menu = OptionMenu(Num_pad_frame, self.admin_user_option_var, *self.local_admin_user_list, command = self.admin_user_option_change)
        Bean_drop_station_selection_option_menu.config(font="Helvitica -30 bold", background= "#e7d2e5", highlightbackground="green", activebackground="#f5edf4") #"#f5edf4"
        print(Bean_drop_station_selection_option_menu.config())
        drop_menu = root.nametowidget(Bean_drop_station_selection_option_menu.menuname)
        drop_menu.config(font="Helvitica -30 bold", background = "#e7d2e5", activebackground="#f5edf4")
        print(drop_menu.config())
        Bean_drop_station_selection_option_menu.grid(column=0, columnspan=3, row=0, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        
            
        Num0_button = Button(Num_pad_frame, text="0", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"0"))
        Num0_button.grid(column=0, columnspan=1, row=5, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num_backspace_button = Button(Num_pad_frame, text=u'\u21e6', bg="#e5989b", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.remove_character_to_entry(mainscreen))
        Num_backspace_button.grid(column=1, columnspan=2, row=5, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
            
        Num1_button = Button(Num_pad_frame, text="1", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"1"))
        Num1_button.grid(column=0, columnspan=1, row=4, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num2_button = Button(Num_pad_frame, text="2", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"2"))
        Num2_button.grid(column=1, columnspan=1, row=4, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num3_button = Button(Num_pad_frame, text="3", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"3"))
        Num3_button.grid(column=2, columnspan=1, row=4, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        
        Num4_button = Button(Num_pad_frame, text="4", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"4"))
        Num4_button.grid(column=0, columnspan=1, row=3, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num5_button = Button(Num_pad_frame, text="5", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"5"))
        Num5_button.grid(column=1, columnspan=1, row=3, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num6_button = Button(Num_pad_frame, text="6", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"6"))
        Num6_button.grid(column=2, columnspan=1, row=3, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        
        Num7_button = Button(Num_pad_frame, text="7", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"7"))
        Num7_button.grid(column=0, columnspan=1, row=2, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num8_button = Button(Num_pad_frame, text="8", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"8"))
        Num8_button.grid(column=1, columnspan=1, row=2, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        Num9_button = Button(Num_pad_frame, text="9", bg="#8cc4ff", font="Helvetica -20", relief= RAISED, bd=2, fg="#04555f", command=lambda: self.add_character_to_entry(mainscreen,"9"))
        Num9_button.grid(column=2, columnspan=1, row=2, rowspan=1, sticky=W+E+N+S, padx=10, pady=10)
        
    def admin_user_option_change(self, event):
        mainscreen.selected_admin_user = self.admin_user_option_var.get()
        mainscreen.entry_widget_user_number = ""
        Entry_white_box.config(textvariable=self.var.set(mainscreen.entry_widget_user_number), show="*", fg="black")
        #Bean_drop_station_selection_option_menu.config(textvariable=mainscreen.entry_widget_user_number)
        pass
        
    # Method to add values to  entry widget on add_customer_frame
    def add_character_to_entry(self, order_class, character):
        if order_class.entry_widget_user_number == "ERROR":
            order_class.entry_widget_user_number = ""
            Entry_white_box.config(textvariable=self.var.set(mainscreen.entry_widget_user_number), show="*", fg="black")
        else:
            pass
        print("Old entry widget user number was: ", order_class.entry_widget_user_number)
        order_class.entry_widget_user_number = order_class.entry_widget_user_number + str(character)
        print("New entry widget user number is: ", order_class.entry_widget_user_number)
        Entry_white_box.config(textvariable=self.var.set(mainscreen.entry_widget_user_number),show="*", fg="black")
        Entry_white_box.focus_set()
        
    def remove_character_to_entry(self, order_class):
        print("Old entry widget user number was: ", order_class.entry_widget_user_number)
        order_class.entry_widget_user_number = order_class.entry_widget_user_number[:-1] #slicing last character from string
        print("New entry widget user number is: ", order_class.entry_widget_user_number)
        Entry_white_box.config(textvariable=self.var.set(mainscreen.entry_widget_user_number))
        Entry_white_box.focus_set()
        
    def verify_admin_user_pin(self):
        print(mainscreen.selected_admin_user, str(mainscreen.entry_widget_user_number))
        if local_admin_user.verify_user(mainscreen.selected_admin_user, str(mainscreen.entry_widget_user_number)):
            print("Correct pwd entered")
            mainscreen.entry_widget_user_number = ""
            mainscreen.pin_success_to_screen(root)
            self.destroy()
        else:
            self.verficiation_attempt_count += 1
            mainscreen.entry_widget_user_number = ""
            Entry_white_box.config(textvariable=self.var.set(mainscreen.entry_widget_user_number), show="*", fg="black")
            if self.verficiation_attempt_count == 3:
                mainscreen.pin_fail_return_screen(root)
                self.destroy()
        pass

    def Launch_SecondFrame(self):  # Linked to button event
        self.destroy()
        number_add()
        SecondFrame(root)

    def OnReturn(self, event):  # Linked to binding return key press
        print("return raised")
        self.destroy()
        number_add()
        SecondFrame(root)

    def options_frame_event(self, event):
        print("[4] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        OptionsFrame(root)
        
    def options_frame_event2(self):
        print("[4] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        OptionsFrame(root)

    def old_orders_frame_event(self, event):
        print("[1] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Old_Orders_Frame(root)
        
    def old_orders_frame_event2(self):
        print("[1] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Old_Orders_Frame(root)

    def add_customer_event(self, event):
        print("[+] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Add_customer_frame(root)
        
    def add_customer_event2(self):
        print("[+] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Add_customer_frame(root)

    def Quit_Event(self, event):  # Temporary program event to quit GUI and end program
        print("quit button pressed")
        root.quit()

    def Reset_Order_Event(self, event):  # Launches new window and asks if reset is needed
        print("[/] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Reset_order_frame(root)
        
    def Reset_Order_Event2(self):  # Launches new window and asks if reset is needed
        print("[/] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Reset_order_frame(root)

    # Launches new window and asks operator to scan cup to remove it from the order
    def remove_cup_frame_event(self, event):
        print("[2] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Remove_Cup_Frame(root)
        
    def remove_cup_frame_event2(self):
        print("[2] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Remove_Cup_Frame(root)

    # Launches new window and asks operator to scan cup to remove it from the order
    def paid_frame_event(self, event):
        print("[5] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Paid_Frame(root)
        
    def paid_frame_event2(self):
        print("[5] pressed")
        mainscreen.threadcondition = 1
        self.destroy()
        Paid_Frame(root)

    def Polling_test(self):
        #_thread.start_new_thread(RFID_polling, ())
        _thread.start_new_thread(rfid_scanner_add, ())
        pass

    def Update_Frame(self):  # dataqueue is not capturing or not updating. Register_cups() method is always running and passing in polling method
        print("Frame trying to update")
        try:
            cupIDdata = dataQueue.get(block=False)
        except queue.Empty:
            # Set at 250 which is same as Polling rate , currently stacking updates....
            self.after(250, self.Update_Frame)
            if main_hardware.updated_hardware_status == True:
                main_hardware.updated_hardware_status = False
                AppFrame(root)
                self.destroy()
            pass
        else:															# else is used to run code after successful try statement
            print("Frame has updated")
            self.destroy()
            AppFrame(root)
        # self.after(250, self.Update_Frame) 								# Set at 250 which is same as Polling rate , currently stacking updates at bottom of method, moved to except statement, stops stacking.


# Inheritted Frame Design
class OptionsFrame(AppFrame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent, width=main_frame_size.width, height=main_frame_size.height, bg="white")
        self.bind("<0xff8d>", self.OnReturn)
        self.bind("<0x0034>", self.options_frame_event)
        # Simple root.quit() event to cancel mainloop() and end program
        self.bind("<BackSpace>", self.Quit_Event)
        # Binds slash to Returning to the main screen from the Options screen
        self.bind("<0xffaf>", self.Options_to_Mainscreen_Return)
        # only works when program is not in fullscreen, focus_force() only works in fullscreen
        self.focus_set()
        # self.focus_force() 														# must set focus to Frame for button binds to work
        self.grid_location(0, 0) 													# setting frame starting location in root window
        # setting row sizes my runnning repeat row configures, rows and columns in .grid start at value of zero (0).
        for r in range(0, 8):
            self.grid_rowconfigure(r, minsize=main_frame_size.row_size_8)
        for c in range(0, 10):
            self.grid_columnconfigure(c, minsize=main_frame_size.column_size_10)
        # self.grid_rowconfigure(0,minsize=50)
        # self.grid_columnconfigure(0, minsize=80)
        # self.grid_columnconfigure(1, minsize=160)
        self.grid(sticky=W+E+N+S)													# Sticky W+E+N+S causes grid to expand to frame size
        self.make_widgets()
        self.make_customer()
        self.Polling_test()
        self.after(250, lambda: self.Update_Frame())

    def make_widgets(self):
        options_title_label = Label(self, text="OPTIONS", bg="white", font="Helvetica -40")
        options_title_label.grid(column=2, columnspan=6, row=0, rowspan=2, sticky=W+E+N+S)
        todays_orders_print_label = Button(
            self, text="SALES TOTALS", bg="#53bcbd", font="Helvetica -20", relief=RAISED, bd=5, command = self.Launch_cafe_totals_frame)
        todays_orders_print_label.grid(column=2, columnspan=6, row=2, sticky=W+E+N+S, pady=3, padx=20)
        customtime_orders_print_label = Button(
            self, text="SOFTWARE UPDATES", bg="#65c3c4", font="Helvetica -20", relief=RAISED, bd=5)
        customtime_orders_print_label.grid(column=2, columnspan=6, row=3, sticky=W+E+N+S, pady=3, padx=20)
        recind_order_label = Button(self, text="CAFE SETTINGS", bg="#75c9c2", font="Helvetica -20", relief=RAISED, bd=5, command = self.Launch_cafe_settings_frame)
        recind_order_label.grid(column=2, columnspan=6, row=4, sticky=W+E+N+S, pady=3, padx=20)
        recind_cups_label = Button(self, text="REPORT ERRORS", bg="#86d0d0", font="Helvetica -20", relief=RAISED, bd=5, command = self.Launch_report_error_frame)
        recind_cups_label.grid(column=2, columnspan=6, row=5, sticky=W+E+N+S, pady=3, padx=20)
        wifi_label = Button(self, text="ADMIN OPTIONS", bg="#9ed9d9", font="Helvetica -20", relief=RAISED, bd=5, command = self.Launch_admin_options_frame)
        wifi_label.grid(column=2, columnspan=6, row=6, sticky=W+E+N+S, pady=3, padx=20)

    def make_customer(self):
        back_label = Button(self, text="Back [/]", bg="yellow", relief=RAISED, bd=5, command = self.Options_to_Mainscreen_Return2)
        back_label.grid(column=0, columnspan=2, row=0, sticky=W+E+N+S)
        beandrop_logo_image_label = Label(
            self, image=beandrop_logo_new_size, bg="white", relief=FLAT)
        beandrop_logo_image_label.grid(column=8, columnspan=2, row=0, rowspan=2, sticky=W+E+N+S)

    def Options_to_Mainscreen_Return(self, event):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        if mainscreen.user_account_number == 0:
            AppFrame(root)											# AppFrame(root) is the main window for no account on order
        else:
            SecondFrame(root)
            
    def Options_to_Mainscreen_Return2(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        if mainscreen.user_account_number == 0:
            AppFrame(root)		
        else:
            AppFrame(root)
            
    def Launch_admin_options_frame(self):
        mainscreen.threadcondition = 0
        self.destroy()
        Admin_Options(root)			
        
    def Launch_cafe_totals_frame(self):
        mainscreen.threadcondition = 0
        self.destroy()
        Cafe_Totals_Frame(root)	

            
    def Launch_cafe_settings_frame(self):
        mainscreen.threadcondition = 0
        mainscreen.pin_success_to_screen = Cafe_Settings
        mainscreen.pin_fail_return_screen = OptionsFrame
        mainscreen.back_button_press_screen = OptionsFrame
        Super_Admin_Pin_Entry(root)
        self.destroy()
        
    def Launch_report_error_frame(self):
        mainscreen.threadcondition = 0
        mainscreen.back_button_press_screen = OptionsFrame
        Report_errors_frame(root)
        self.destroy()
            
    def ProcessingEvent2(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 1
        mainscreen.variable_text_output = "Outputting CSV File to beandrop.company@gmail.com"
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        Electronic_Processing_Frame(root)


class Old_Orders_Frame(AppFrame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent, width=main_frame_size.width, height=main_frame_size.height, bg="white")
        # Binds slash to Returning to the main screen from the Options screen
        self.bind("<0xffaf>", self.Old_Orders_to_Mainscreen_Return)
        # Binds the plus button to updating the offset numbers which update the screen with latest orders
        self.bind("<0xffab>", self.Update_Offset_Decrease)
        # Binds the minus (correction - needs checking as I cannot see it with data yet) button to updating the offset numbers which update the screen with older orders
        self.bind("<0xffad>", self.Update_Offset_Increase)
        # only works when program is not in fullscreen, focus_force() only works in fullscreen
        self.focus_set()
        # self.focus_force() 														# must set focus to Frame for button binds to work
        self.grid_location(0, 0) 													# setting frame starting location in root window
        # setting row sizes my runnning repeat row configures, rows and columns in .grid start at value of zero (0).
        for r in range(0, 8):
            self.grid_rowconfigure(r, minsize=main_frame_size.row_size_8)
        for c in range(0, 10):
            self.grid_columnconfigure(c, minsize=main_frame_size.column_size_10)
        # self.grid_rowconfigure(0,minsize=50)
        # self.grid_columnconfigure(0, minsize=80)
        # self.grid_columnconfigure(1, minsize=160)
        self.grid(sticky=W+E+N+S)													# Sticky W+E+N+S causes grid to expand to frame size
        self.make_widgets()
        self.make_customer()
        mainscreen.threadcondition = 1 # Pause any ongoing Polling
        #self.Polling_test() #removed as I believe it is historical. Polling should not be occuring during Old Orders Frame
        self.after(250, lambda: self.Update_Frame())

    def make_widgets(self):        
        # Using for statement to run above orders and collect same exceptions in a single try statement -----------------------------------
        dictionary_of_offset_order_classes = {1:first_offset_order_class, 2:second_offset_order_class, 3:third_offset_order_class, 4:fourth_offset_order_class, 5:fith_offset_order_class}
        dictionary_of_offset_number_classes_offset_options = {1:main_offset_class.first_offset, 2:main_offset_class.second_offset, 3:main_offset_class.third_offset, 4:main_offset_class.fourth_offset, 5:main_offset_class.fith_offset}
        for i in range(1,6):
            try:
                dictionary_of_offset_order_classes[i].update_offset_order_class(local_db.return_historic_order_from_offset_ldb(dictionary_of_offset_number_classes_offset_options[i]))
                print(dictionary_of_offset_order_classes[i])
            except Exception as e:
                print(e)
                offset_order_class_temp_variables = ("","","","","","",0,0) #Blank variables to be displayed...
                dictionary_of_offset_order_classes[i].update_offset_order_class(offset_order_class_temp_variables)
        
        print(first_offset_order_class)
        options_title_label = Label(self, text="OLD ORDERS", bg="white", font="Helvetica -40")
        options_title_label.grid(column=2, columnspan=6, row=0, rowspan=1, sticky=W+E+N+S)
        
        #----------------- Order Selection Options Frame
        Order_selection_frame = Frame(self, width=main_frame_size.column_size_10*8, height=main_frame_size.row_size_8*6, bg="white", relief=FLAT)
        Order_selection_frame.grid(column=0, columnspan=8, row=1, rowspan=6, sticky=W+E+N+S)
        for c in range(0, 16):
            Order_selection_frame.grid_columnconfigure(c, minsize=main_frame_size.column_size_10/2)
        for r in range(0, 12):
            Order_selection_frame.grid_rowconfigure(r, minsize=main_frame_size.row_size_8/2)

        order_number_table_label = Label(Order_selection_frame, text="| ORDER # |",
                                         bg="white", font="Helvetica -20", pady=5, anchor=S)
        order_number_table_label.grid(column=1, columnspan=4, row=1,
                                      rowspan=1, padx=(10, 0), sticky=W+E+S)
        order_datetime_table_label = Label(
            Order_selection_frame, text="| DATE & TIME |", bg="white", font="Helvetica -20", pady=5, anchor=S)
        order_datetime_table_label.grid(column=5, columnspan=6, row=1, rowspan=1, sticky=W+E+N+S)
        number_of_cups_table_lable = Label(
            Order_selection_frame, text="| CUPS |", bg="white", font="Helvetica -20", pady=5, anchor=S)
        number_of_cups_table_lable.grid(column=11, columnspan=2, row=1, rowspan=1, sticky=W+E+N+S)
        order_value_table_label = Label(
            Order_selection_frame, text="| PAID |", bg="white", font="Helvetica -20", pady=5, anchor=S)
        order_value_table_label.grid(column=13, columnspan=3, row=1,
                                     rowspan=1, padx=(0, 10), sticky=W+E+N+S)

        last_order_offset_1_label = Button(Order_selection_frame, text=str(first_offset_order_class.order_id_POS_ldb).zfill(
            8), bg="#53bcbd", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset.first_offset))			# .zfill(8) is used to pad zeros on the end of a string.
        last_order_offset_1_label.grid(column=1, columnspan=4, row=2, rowspan=2,
                                       sticky=W+E+N+S, padx=(10, 0), pady=5)
        last_order_offset_1_label2 = Button(Order_selection_frame, text=first_offset_order_class.order_datetime, bg="#53bcbd", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset.first_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label2.grid(column=5, columnspan=6, row=2, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_1_label3 = Button(Order_selection_frame, text=first_offset_order_class.cups_registered_ldb, bg="#53bcbd", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset.first_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label3.grid(column=11, columnspan=2, row=2, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_1_label4 = Button(Order_selection_frame, text=("£", format(first_offset_order_class.value_taken_ldb,'.2f')), bg="#53bcbd", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset.first_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label4.grid(column=13, columnspan=3, row=2, rowspan=2, 
                                        sticky=W+E+N+S, padx=(0, 10), pady=5)

        last_order_offset_2_label = Button(Order_selection_frame, text=str(second_offset_order_class.order_id_POS_ldb).zfill(
            8), bg="#65c3c4", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.second_offset))			# .zfill(8) is used to pad zeros on the end of a string.
        last_order_offset_2_label.grid(column=1, columnspan=4, row=4, rowspan=2,
                                       sticky=W+E+N+S, padx=(10, 0), pady=5)
        last_order_offset_2_label2 = Button(Order_selection_frame, text=second_offset_order_class.order_datetime, bg="#65c3c4", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.second_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_2_label2.grid(column=5, columnspan=6, row=4, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_2_label3 = Button(Order_selection_frame, text=second_offset_order_class.cups_registered_ldb, bg="#65c3c4", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.second_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_2_label3.grid(column=11, columnspan=2, row=4, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_2_label4 = Button(Order_selection_frame, text=("£", format(second_offset_order_class.value_taken_ldb,'.2f')), bg="#65c3c4", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.second_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_2_label4.grid(column=13, columnspan=3, row=4, rowspan=2,
                                        sticky=W+E+N+S, padx=(0, 10), pady=5)

        last_order_offset_3_label = Button(Order_selection_frame, text=str(third_offset_order_class.order_id_POS_ldb).zfill(
            8), bg="#75c9c2", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.third_offset))			# .zfill(8) is used to pad zeros on the end of a string.
        # padx=(10,0) uses a tuple to represent padding on the left and right
        last_order_offset_3_label.grid(column=1, columnspan=4, row=6, rowspan=2, 
                                       sticky=W+E+N+S, padx=(10, 0), pady=5)
        last_order_offset_3_label2 = Button(Order_selection_frame, text=third_offset_order_class.order_datetime, bg="#75c9c2", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.third_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_3_label2.grid(column=5, columnspan=6, row=6, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_3_label3 = Button(Order_selection_frame, text=third_offset_order_class.cups_registered_ldb, bg="#75c9c2", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.third_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_3_label3.grid(column=11, columnspan=2, row=6, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_3_label4 = Button(Order_selection_frame, text=("£", format(third_offset_order_class.value_taken_ldb,'.2f')), bg="#75c9c2", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.third_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_3_label4.grid(column=13, columnspan=3, row=6, rowspan=2, 
                                        sticky=W+E+N+S, padx=(0, 10), pady=5)

        last_order_offset_4_label = Button(Order_selection_frame, text=str(fourth_offset_order_class.order_id_POS_ldb).zfill(
            8), bg="#86d0d0", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.fourth_offset))			# .zfill(8) is used to pad zeros on the end of a string.
        last_order_offset_4_label.grid(column=1, columnspan=4, row=8, rowspan=2, 
                                       sticky=W+E+N+S, padx=(10, 0), pady=5)
        last_order_offset_4_label2 = Button(Order_selection_frame, text=fourth_offset_order_class.order_datetime, bg="#86d0d0", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.fourth_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_4_label2.grid(column=5, columnspan=6, row=8, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_4_label3 = Button(Order_selection_frame, text=fourth_offset_order_class.cups_registered_ldb, bg="#86d0d0", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.fourth_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_4_label3.grid(column=11, columnspan=2, row=8, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_4_label4 = Button(Order_selection_frame, text=("£", format(fourth_offset_order_class.value_taken_ldb,'.2f')), bg="#86d0d0", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_offset_order(main_offset_class.fourth_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_4_label4.grid(column=13, columnspan=3, row=8, rowspan=2, 
                                        sticky=W+E+N+S, padx=(0, 10), pady=5)

        last_order_offset_5_label = Button(Order_selection_frame, text=' '.join(map(str, check_last_order_offset_order_id_overall_local(main_offset.fith_offset))).zfill(
            8), bg="#9ed9d9", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_order(main_offset.fith_offset))			# .zfill(8) is used to pad zeros on the end of a string.
        last_order_offset_5_label.grid(column=1, columnspan=4, row=10, rowspan=2, 
                                       sticky=W+E+N+S, padx=(10, 0), pady=5)
        last_order_offset_5_label2 = Button(Order_selection_frame, text=check_last_order_offset_order_datetime(
            main_offset.fith_offset), bg="#9ed9d9", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_order(main_offset.fith_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_5_label2.grid(column=5, columnspan=6, row=10, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_5_label3 = Button(Order_selection_frame, text=check_last_order_offset_cups_registered_local(
            main_offset.fith_offset), bg="#9ed9d9", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_order(main_offset.fith_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_5_label3.grid(column=11, columnspan=2, row=10, rowspan=2, sticky=W+E+N+S, pady=5)
        last_order_offset_5_label4 = Button(Order_selection_frame, text=("£", check_last_order_offset_order_value_local(
            main_offset.fith_offset)), bg="#9ed9d9", relief=RAISED, padx=5, font="Helvetica -20", command= lambda: self.select_old_individual_order(main_offset.fith_offset))			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_5_label4.grid(column=13, columnspan=3, row=10, rowspan=2, 
                                        sticky=W+E+N+S, padx=(0, 10), pady=5)

        older_orders_label = Button(self, text="OLDER ORDERS [-]", bg="#33BCFF", relief=RAISED, command = self.Update_Offset_Increase2)
        older_orders_label.grid(column=8, columnspan=2, row=5, rowspan=1, sticky=W+E+N+S, padx = 20)
        latest_orders_label = Button(self, text="LATEST ORDERS [+]", bg="#75FF00", relief=RAISED, command = self.Update_Offset_Decrease2)
        latest_orders_label.grid(column=8, columnspan=2, row=3, rowspan=1, sticky=W+E+N+S, padx = 20)

    def make_customer(self):
        back_label = Button(self, text="Back [/]", bg="yellow", relief=RAISED, bd=5, command = self.Old_Orders_to_Mainscreen_Return2)
        back_label.grid(column=0, columnspan=2, row=0, sticky=W+E+N+S)
        beandrop_logo_image_label = Label(
            self, image=beandrop_logo_new_size, bg="white", relief=FLAT)
        beandrop_logo_image_label.grid(column=8, columnspan=2, row=0, rowspan=2, sticky=W+E+N+S)

    def Old_Orders_to_Mainscreen_Return(self, event):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        reset_offset()
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        if mainscreen.user_account_number == 0:
            AppFrame(root)											# AppFrame(root) is the main window for no account on order
        else:
            SecondFrame(root)
            
    def Old_Orders_to_Mainscreen_Return2(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        reset_offset()
        main_offset_class.reset_offset() # Resets the offset_numbers_class imported from POS_local_db_class.py
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        if mainscreen.user_account_number == 0:
            AppFrame(root)											# AppFrame(root) is the main window for no account on order
        else:
            SecondFrame(root)
            
    def select_old_individual_order(self,option_number):
        main_offset.selected_offset = option_number
        print("selected offset number is: ", main_offset.selected_offset)
        self.destroy()
        Individual_Order_Screen(root)

    def select_old_individual_offset_order(self, option_number):
        global number_of_cups_found_in_refund
        global number_of_cups_in_old_order
        number_of_cups_found_in_refund = 1 # Used for dictionary of cups found. 1 is equivalent to a reset
        cups_found_in_refund_dictionary.clear() #Clearing dictionary of RFID values found
        number_of_cups_in_old_order = 0
        cups_in_old_order_dictionary.clear() #Clearing dictionary of RFID values found
        main_offset_class.selected_offset = option_number
        print("selected offset_number_class is: ", main_offset_class.selected_offset)
        try:
            selected_offset_order_class.update_offset_order_class(local_db.return_historic_order_from_offset_ldb(main_offset_class.selected_offset))
            self.destroy()
            Individual_Order_Screen(root)
        except Exception as e:
            print("Screen / Button will not progress to individual order as none order selected with error: ",e)

    def Update_Offset_Increase(self, event):
        add_to_offset()
        self.destroy()
        Old_Orders_Frame(root)
        
    def Update_Offset_Increase2(self):
        add_to_offset()
        main_offset_class.add_to_offset() #Adding to offset_numbers_class
        self.destroy()
        Old_Orders_Frame(root)

    def Update_Offset_Decrease(self, event):
        minus_from_offset()
        self.destroy()
        Old_Orders_Frame(root)
        
    def Update_Offset_Decrease2(self):
        minus_from_offset()
        main_offset_class.minus_from_offset() #Minusing from offset_numbers_class
        self.destroy()
        Old_Orders_Frame(root)

class Individual_Order_Screen(AppFrame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent, width=main_frame_size.width, height=main_frame_size.height, bg="white")
        self.bind("<0xff8d>", self.OnReturn)
        self.bind("<0x0034>", self.options_frame_event)
        # Simple root.quit() event to cancel mainloop() and end program
        self.bind("<BackSpace>", self.Quit_Event)
        # Binds slash to Returning to the main screen from the Options screen
        self.bind("<0xffaf>", self.Individual_to_old_orders_frame)
        # only works when program is not in fullscreen, focus_force() only works in fullscreen
        self.focus_set()
        # self.focus_force() 														# must set focus to Frame for button binds to work
        self.grid_location(0, 0) 													# setting frame starting location in root window
        # setting row sizes my runnning repeat row configures, rows and columns in .grid start at value of zero (0).
        for r in range(0, 8):
            self.grid_rowconfigure(r, minsize=main_frame_size.row_size_8)
        for c in range(0, 10):
            self.grid_columnconfigure(c, minsize=main_frame_size.column_size_10)
        mainscreen.threadcondition = 1 #Pause any RFID polling still ongoing
        self.grid(sticky=W+E+N+S)													# Sticky W+E+N+S causes grid to expand to frame size
        self.make_widgets()
        self.make_customer()
        self.after(250, lambda: self.Update_Frame())

    def make_widgets(self):
        # global cups_in_old_order_dictionary
        global number_of_cups_in_old_order
        selected_offset_order_class.update_offset_order_class(local_db.return_historic_order_from_offset_ldb(main_offset_class.selected_offset))
        update_cup_dictionary_variables = (selected_offset_order_class.order_id_POS_ldb,"")
        print("number of cups in old order before individual orders screen update",number_of_cups_in_old_order)
        number_of_cups_in_old_order = update_cups_in_old_order_dict2(local_db, update_cup_dictionary_variables, cups_in_old_order_dictionary)
        print("number of cups in old order after individual orders screen update",number_of_cups_in_old_order)
        print("current cups in cups_in_old_order_dictionary are: ",cups_in_old_order_dictionary)
        options_title_label = Label(self, text="HISTORIC ORDER", bg="white", font="Helvetica -40")
        options_title_label.grid(column=2, columnspan=6, row=0, sticky=W+E+N+S)
        selected_order_number_label = Label(
            self, text=("ORDER #: " + str(selected_offset_order_class.order_id_POS_ldb).zfill(
            8)), bg="white", font="Helvetica -30", fg="#04555f")
        selected_order_number_label.grid(column=2, columnspan=6, row=1, sticky=W+E+N)
        
        # bottom frame widget for containing payment numbers
        bottom_frame = Frame(self, width=900, height=400, bg="#86d0d0", bd=5, relief=RAISED)
        bottom_frame.grid(column=0, columnspan=10, row=2, rowspan=5)
        for c in range(0, 20):
            bottom_frame.grid_columnconfigure(c, minsize=44)
        for r in range(0, 10):
            bottom_frame.grid_rowconfigure(r, minsize=39)
            
        
        order_number_table_label = Label(bottom_frame, text="CUSTOMER ACCOUNT #:",
                                         bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        order_number_table_label.grid(column=1, columnspan=8, row=0,
                                      rowspan=1, sticky=E+N+S)
        order_datetime_table_label = Label(
            bottom_frame, text="DATE & TIME:", bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        order_datetime_table_label.grid(column=1, columnspan=8, row=1, rowspan=1, sticky=E+N+S)
        number_of_cups_table_lable = Label(
            bottom_frame, text="- CUPS -", bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        number_of_cups_table_lable.grid(column=1, columnspan=19, row=2, rowspan=1, sticky=W+E+N+S)
        number_of_cups_table_lable = Label(
            bottom_frame, text="CUPS FROM CUSTOMER ACCOUNT:", bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        number_of_cups_table_lable.grid(column=1, columnspan=8, row=3, rowspan=1, sticky=E+N+S)
        number_of_cups_table_lable = Label(
            bottom_frame, text="NEW CUPS:", bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        number_of_cups_table_lable.grid(column=1, columnspan=8, row=4, rowspan=1, sticky=E+N+S)
        total_number_of_cups_table_lable = Label(
            bottom_frame, text="TOTAL CUPS IN ORDER:", bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        total_number_of_cups_table_lable.grid(column=1, columnspan=8, row=5, rowspan=1, sticky=E+N+S)
        order_value_table_label = Label(
            bottom_frame, text="PAID BY CUSTOMER:", bg="#86d0d0", font="Helvetica -22", fg="#04555f", pady=5, anchor=S)
        order_value_table_label.grid(column=1, columnspan=8, row=6, rowspan=1, sticky=E+N+S)
                                     
        
        last_order_offset_1_label = Label(bottom_frame, text=selected_offset_order_class.user_unique_ID_ldb, relief=FLAT, padx=5, font="Helvetica -15", wraplength=450)			# .zfill(8) is used to pad zeros on the end of a string.
        last_order_offset_1_label.grid(column=9, columnspan=10, row=0,
                                       sticky=W+E+N+S, pady=5)
        last_order_offset_1_label2 = Label(bottom_frame, text=selected_offset_order_class.order_datetime, relief=FLAT, padx=5, font="Helvetica -22")			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label2.grid(column=9, columnspan=10, row=1, sticky=W+E+N+S, pady=5)
        last_order_offset_1_label3 = Label(bottom_frame, text=format(selected_offset_order_class.account_cups_calculated,'.0f'), relief=FLAT, padx=5, font="Helvetica -22")			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label3.grid(column=9, columnspan=10, row=3, sticky=W+E+N+S, pady=5)
        last_order_offset_1_label4 = Label(bottom_frame, text=format(selected_offset_order_class.new_cups_calculated,'.0f'), relief=FLAT, padx=5, font="Helvetica -22")			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label4.grid(column=9, columnspan=10, row=4, sticky=W+E+N+S, pady=5)
        last_order_offset_1_label5 = Label(bottom_frame, text=selected_offset_order_class.cups_registered_ldb, relief=FLAT, padx=5, font="Helvetica -22")			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label5.grid(column=9, columnspan=10, row=5, sticky=W+E+N+S, pady=5)
        last_order_offset_1_label6 = Label(bottom_frame, text=("£", format(selected_offset_order_class.value_taken_ldb,'.2f')), relief=FLAT, padx=5, font="Helvetica -22")			# The use of '*' infront of item unpacks and removes curly brackets
        last_order_offset_1_label6.grid(column=9, columnspan=10, row=6,
                                        sticky=W+E+N+S, pady=5)
            
        print_individual_order_button = Button(
            bottom_frame, text="PRINT RECEIPT", bg="#beea86", relief=RAISED, bd=3, padx=5, font="Helvetica -25", fg="#04555f", wraplength=150, command=self.Print_old_order)
        print_individual_order_button.grid(column=2, columnspan=4, row=7, rowspan=3,
                                        sticky=W+E+N+S, padx=10, pady=10)
        print_individual_order_button = Button(
            bottom_frame, text="REFUND ORDER", bg="#e5989b", relief=RAISED, bd=3, padx=5, font="Helvetica -25", fg="#04555f", wraplength=150, command=self.Refund_Frame_Launch)
        print_individual_order_button.grid(column=8, columnspan=4, row=7, rowspan=3,
                                        sticky=W+E+N+S, padx=10, pady=10)
        print_individual_order_button = Button(
            bottom_frame, text="SWITCH CUPS", bg="#8cc4ff", relief=RAISED, bd=3, padx=5, font="Helvetica -25", fg="#04555f", wraplength=150, command=print("printing"))
        print_individual_order_button.grid(column=13, columnspan=4, row=7, rowspan=3,
                                        sticky=W+E+N+S, padx=10, pady=10)

    def make_customer(self):
        back_label = Button(self, text="Back [/]", bg="yellow", relief=RAISED, bd=5, command = self.Individual_to_old_orders_frame2)
        back_label.grid(column=0, columnspan=2, row=0, sticky=W+E+N+S)
        beandrop_logo_image_label = Label(
            self, image=beandrop_logo_new_size, bg="white", relief=FLAT)
        beandrop_logo_image_label.grid(column=8, columnspan=2, row=0, rowspan=2, sticky=W+E+N+S)

    def Individual_to_old_orders_frame(self, event):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        Old_Orders_Frame(root)
            
    def Individual_to_old_orders_frame2(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        Old_Orders_Frame(root)
        
    def Print_old_order(self):
        temporary_mainscreen_class.user_account_number = selected_offset_order_class.user_unique_ID_ldb
        temporary_mainscreen_class.POS_hash = selected_offset_order_class.pos_hash_id_ldb
        temporary_mainscreen_class.local_order_id = selected_offset_order_class.order_id_overall_ldb
        print("Temp user_account_number: ",temporary_mainscreen_class.user_account_number)#temporary_mainscreen_class.local_order_id = 
        temporary_mainscreen_class.amount_of_RFID_Numbers_Registered = selected_offset_order_class.cups_registered_ldb
        print("Temp number of cups registered is: ",temporary_mainscreen_class.amount_of_RFID_Numbers_Registered)
        # MultiP = Process(target=print_new_customer_receipt, args = (temporary_mainscreen_class,))
        # MultiP.start()
        POS_thermal_printer_class = bean_drop_thermal_printer_class("/dev/ttyUSB0", 19200, 5, 2.168)
        t1 = Process(target=POS_thermal_printer_class.print_customer_reciept, args=(temporary_mainscreen_class,selected_offset_order_class.order_datetime)) #Thermal Printer Raspi Commands with new printer class and QR Code
        t1.start()
        
    def ProcessingEvent2(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        temporary_mainscreen_class.user_account_number = ' '.join(map(str, check_user_unique_ID_local(main_offset.first_offset))).zfill(8)
        mainscreen.threadcondition = 1
        variable_text_output_variables = ("Refunding order to user account: ", str(temporary_mainscreen_class.user_account_number))
        mainscreen.variable_text_output = ("".join(variable_text_output_variables))
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        #Electronic_Processing_Frame(root)
        Refund_Cup_Frame(root)
        
    def Refund_Frame_Launch(self):
        try:
            print(server1.return_cup_ownership_for_refunds(selected_offset_order_class, cups_in_old_order_dictionary, number_of_cups_in_old_order, updated_cups_in_old_order_dictionary))    #selected_offset_order_class, rfid_dictionary, rfid_dictionary_length, updated_rfid_dictionary
            number_of_cups_still_owned = server1.return_cup_ownership_for_refunds(selected_offset_order_class, cups_in_old_order_dictionary, number_of_cups_in_old_order, updated_cups_in_old_order_dictionary)   #selected_offset_order_class, rfid_dictionary, rfid_dictionary_length, updated_rfid_dictionary
            print("NEW: Priting number of cups still owned...",number_of_cups_still_owned)
            print("printing cups in old order dictionary",cups_in_old_order_dictionary)
            print("printing cups in updated dictionary",updated_cups_in_old_order_dictionary)
            if number_of_cups_in_old_order > number_of_cups_still_owned and number_of_cups_still_owned > 0:
                variable_text_output_variables = (str(number_of_cups_in_old_order - number_of_cups_still_owned), "/", str(number_of_cups_in_old_order), " IN ORIGINAL ORDER HAVE BEEN REFUNDED ALREADY")
                mainscreen.variable_text_output = ("".join(variable_text_output_variables))
                cups_in_old_order_dictionary.clear()
                cups_found_in_refund_dictionary.clear()                     #clearing dictionary just in case.... Should have already been cleared...
                for i in updated_cups_in_old_order_dictionary:
                    cups_in_old_order_dictionary[i] = updated_cups_in_old_order_dictionary[i]
                Refund_Cup_Frame(root)
                self.destroy()  #This self.destroy() call is placed after the Refund_Cup_Frame(root) - this is not normal.... I am doing this because if I call self.destroy first it seems to lag and display a grey screen... Cancelling after might cause issues.... non seen so far. Lag still apparent, but no grey screen...

            elif number_of_cups_still_owned == 0:
                variable_text_output_variables = ("ORDER HAS BEEN FULLY REFUNDED ALREADY")
                mainscreen.variable_text_output = ("".join(variable_text_output_variables))
                self.destroy()
                Electronic_Processing_Frame(root)
            elif number_of_cups_in_old_order == number_of_cups_still_owned:
                Refund_Cup_Frame(root)
                self.destroy()  #This self.destroy() call is placed after the Refund_Cup_Frame(root) - this is not normal.... I am doing this because if I call self.destroy first it seems to lag and display a grey screen... Cancelling after might cause issues.... non seen so far. Lag still apparent, but no grey screen...
        except Exception as error:
            print ("Exception raised during refund Frame launch. Error is: ", error)
            print(type(error))
            print(error.args)
            traceback.print_exc()

# Frame to type in customer details to register to system
class Add_customer_frame(AppFrame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent, width=main_frame_size.width, height=main_frame_size.height, bg="light blue")
        # only works when program is not in fullscreen, focus_force() only works in fullscreen
        self.focus_set()
        # self.focus_force() 														# must set focus to Frame for button binds to work
        self.grid_location(0, 0) 													# setting frame starting location in root window
        # setting row sizes my runnning repeat row configures, rows and columns in .grid start at value of zero (0).
        for r in range(0, 8):
            self.grid_rowconfigure(r, minsize=main_frame_size.row_size_8)
        for c in range(0, 10):
            self.grid_columnconfigure(c, minsize=main_frame_size.column_size_10)
        self.grid(sticky=W+E+N+S)													# Sticky W+E+N+S causes grid to expand to frame size
        self.make_widgets()
        self.make_keyboard()

        # Variable which is linked to entry widget
        self.var = StringVar()  # linked entry value to customer entry widget, linked to .get() function
        self.var.set(mainscreen.entry_widget_user_number)  # setting the initial entry value to nothing

        # Customer entry widget operation
        global customer_entry_widget
        customer_entry_widget = Entry(self, bg="white", bd=5, font="Helvitica -20 bold")
        customer_entry_widget.grid(column=2, columnspan=6, row=3, sticky=W+E+N+S)
        # Setting up entry variable to be called later on
        customer_entry_widget.config(textvariable=self.var)
        customer_entry_widget.focus_set()
        # Adds customer to main page (plus button is binded)
        customer_entry_widget.bind("<0xffab>", (lambda event: self.Add_customer_details_event()))
        # Cancels adding customer (slash button is binded)
        customer_entry_widget.bind("<0xffaf>", self.Cancel_add_customer_event)
        
        #----- Addition of QR Code Reader -------
        mainscreen.threadcondition = 1 #Thread condition of 1 will pause polling and zero will cancel the QR Camera
        mainscreen.thread_qr_code = True
        POS_QR_Scanner.qr_scanning_on = True
        print("changed POS_QR_SCanner.qr_scanning_on to true, from myside it reads as: ", POS_QR_Scanner.qr_scanning_on)
        self.QR_Code_Read()
        self.after(250, lambda: self.Update_Frame())

    def make_widgets(self):
        beandrop_logo_image_label = Label(
            self, image=beandrop_logo_new_size, bg="white", relief=RAISED)
        beandrop_logo_image_label.grid(column=8, columnspan=2, row=0, rowspan=2, sticky=W+E+N+S)

        Add_customer_label = Label(self, text="ADD CUSTOMER", bg="light blue", font="Helvetica -40")
        Add_customer_label.grid(column=2, columnspan=6, row=1, sticky=W+E+N+S)
        instructions_label = Label(self, text="Enter 20 digit customer number",
                                   font="Helvetica -20 italic", bg="light blue")
        instructions_label.grid(column=2, columnspan=6, row=2, sticky=W+E+N+S)
        add_customer_button_label = Button(
            self, text="ADD [+]", bg="#75FF00", relief=RAISED, bd=5, pady=5, font="Helvetica -20", command = self.Add_customer_details_event)
        add_customer_button_label.grid(column=6, columnspan=3, row=4, rowspan=2, sticky=W+E+N, pady=8)
        cancel_customer_button_label = Button(
            self, text="CANCEL [/]", bg="red", relief=RAISED, bd=5, pady=5, font="Helvetica -20", command = self.Cancel_add_customer_event2)
        cancel_customer_button_label.grid(column=1, columnspan=3, row=4, rowspan=2, sticky=W+E+N, pady=8)

    def make_keyboard(self):
        # bottom frame widget for containing payment numbers
        bottom_frame = Frame(self, width=780, height=120, bg="#daf0dc", bd=2, relief=RAISED)
        bottom_frame.grid(column=0, columnspan=10, row=5, rowspan=3)
        for c in range(0, 26):
            bottom_frame.grid_columnconfigure(c, minsize=30)
        for r in range(0, 3):
            bottom_frame.grid_rowconfigure(r, minsize=40)
        
        if mainscreen.switching_value == 0:
            #Top of QWERTY KEYBOARD--------------------------------------
            q_letter_button = Button(
                bottom_frame, text="q", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"q"))
            q_letter_button.grid(column=0, row=0, columnspan=2, sticky=W+E+N+S)
            w_letter_button = Button(
                bottom_frame, text="w", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"w"))
            w_letter_button.grid(column=2, row=0, columnspan=2, sticky=W+E+N+S)
            e_letter_button = Button(
                bottom_frame, text="e", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"e"))
            e_letter_button.grid(column=4, row=0, columnspan=2, sticky=W+E+N+S)
            r_letter_button = Button(
                bottom_frame, text="r", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"r"))
            r_letter_button.grid(column=6, row=0, columnspan=2, sticky=W+E+N+S)
            t_letter_button = Button(
                bottom_frame, text="t", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"t"))
            t_letter_button.grid(column=8, row=0, columnspan=2, sticky=W+E+N+S)
            y_letter_button = Button(
                bottom_frame, text="y", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"y"))
            y_letter_button.grid(column=10, row=0, columnspan=2, sticky=W+E+N+S)
            u_letter_button = Button(
                bottom_frame, text="u", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"u"))
            u_letter_button.grid(column=12, row=0, columnspan=2, sticky=W+E+N+S)
            i_letter_button = Button(
                bottom_frame, text="i", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"i"))
            i_letter_button.grid(column=14, row=0, columnspan=2, sticky=W+E+N+S)
            o_letter_button = Button(
                bottom_frame, text="o", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"o"))
            o_letter_button.grid(column=16, row=0, columnspan=2, sticky=W+E+N+S)
            p_letter_button = Button(
                bottom_frame, text="p", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"p"))
            p_letter_button.grid(column=18, row=0, columnspan=2, sticky=W+E+N+S)
            Num7_letter_button = Button(
                bottom_frame, text="7", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"7"))
            Num7_letter_button.grid(column=20, row=0, columnspan=2, sticky=W+E+N+S)
            Num8_letter_button = Button(
                bottom_frame, text="8", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"8"))
            Num8_letter_button.grid(column=22, row=0, columnspan=2, sticky=W+E+N+S)
            Num9_letter_button = Button(
                bottom_frame, text="9", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"9"))
            Num9_letter_button.grid(column=24, row=0, columnspan=2, sticky=W+E+N+S)
            
            
            #Middle of QWERTY KEYBOARD--------------------------------------
            a_letter_button = Button(
                bottom_frame, text="a", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"a"))
            a_letter_button.grid(column=1, row=1, columnspan=2, sticky=W+E+N+S)
            s_letter_button = Button(
                bottom_frame, text="s", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"s"))
            s_letter_button.grid(column=3, row=1, columnspan=2, sticky=W+E+N+S)
            d_letter_button = Button(
                bottom_frame, text="d", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"d"))
            d_letter_button.grid(column=5, row=1, columnspan=2, sticky=W+E+N+S)
            f_letter_button = Button(
                bottom_frame, text="f", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"f"))
            f_letter_button.grid(column=7, row=1, columnspan=2, sticky=W+E+N+S)
            g_letter_button = Button(
                bottom_frame, text="g", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"g"))
            g_letter_button.grid(column=9, row=1, columnspan=2, sticky=W+E+N+S)
            h_letter_button = Button(
                bottom_frame, text="h", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"h"))
            h_letter_button.grid(column=11, row=1, columnspan=2, sticky=W+E+N+S)
            j_letter_button = Button(
                bottom_frame, text="j", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"j"))
            j_letter_button.grid(column=13, row=1, columnspan=2, sticky=W+E+N+S)
            k_letter_button = Button(
                bottom_frame, text="k", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"k"))
            k_letter_button.grid(column=15, row=1, columnspan=2, sticky=W+E+N+S)
            l_letter_button = Button(
                bottom_frame, text="l", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"l"))
            l_letter_button.grid(column=17, row=1, columnspan=2, sticky=W+E+N+S)
            Num4_letter_button = Button(
                bottom_frame, text="4", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"4"))
            Num4_letter_button.grid(column=20, row=1, columnspan=2, sticky=W+E+N+S)
            Num5_letter_button = Button(
                bottom_frame, text="5", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"5"))
            Num5_letter_button.grid(column=22, row=1, columnspan=2, sticky=W+E+N+S)
            Num6_letter_button = Button(
                bottom_frame, text="6", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"6"))
            Num6_letter_button.grid(column=24, row=1, columnspan=2, sticky=W+E+N+S)
            
            #Middle of QWERTY KEYBOARD--------------------------------------
            caps_letter_button = Button(
                bottom_frame, text=u'\u21e7', bg="#de6262", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.Caps(mainscreen))
            caps_letter_button.grid(column=0, row=2, columnspan=2, sticky=W+E+N+S)
            z_letter_button = Button(
                bottom_frame, text="z", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"z"))
            z_letter_button.grid(column=2, row=2, columnspan=2, sticky=W+E+N+S)
            x_letter_button = Button(
                bottom_frame, text="x", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"x"))
            x_letter_button.grid(column=4, row=2, columnspan=2, sticky=W+E+N+S)
            c_letter_button = Button(
                bottom_frame, text="c", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"c"))
            c_letter_button.grid(column=6, row=2, columnspan=2, sticky=W+E+N+S)
            v_letter_button = Button(
                bottom_frame, text="v", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"v"))
            v_letter_button.grid(column=8, row=2, columnspan=2, sticky=W+E+N+S)
            b_letter_button = Button(
                bottom_frame, text="b", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"b"))
            b_letter_button.grid(column=10, row=2, columnspan=2, sticky=W+E+N+S)
            n_letter_button = Button(
                bottom_frame, text="n", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"n"))
            n_letter_button.grid(column=12, row=2, columnspan=2, sticky=W+E+N+S)
            n_letter_button = Button(
                bottom_frame, text="m", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"m"))
            n_letter_button.grid(column=14, row=2, columnspan=2, sticky=W+E+N+S)
            backspace_letter_button = Button(
                bottom_frame, text=u'\u21e6', bg="#de6262", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.remove_character_to_entry(mainscreen))
            backspace_letter_button.grid(column=16, row=2, columnspan=2, sticky=W+E+N+S)
            Num0_letter_button = Button(
                bottom_frame, text="0", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"0"))
            Num0_letter_button.grid(column=18, row=2, columnspan=2, sticky=W+E+N+S)
            Num1_letter_button = Button(
                bottom_frame, text="1", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"1"))
            Num1_letter_button.grid(column=20, row=2, columnspan=2, sticky=W+E+N+S)
            Num2_letter_button = Button(
                bottom_frame, text="2", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"2"))
            Num2_letter_button.grid(column=22, row=2, columnspan=2, sticky=W+E+N+S)
            Num3_letter_button = Button(
                bottom_frame, text="3", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"3"))
            Num3_letter_button.grid(column=24, row=2, columnspan=2, sticky=W+E+N+S)
        elif mainscreen.switching_value == 1:
            #Top of QWERTY KEYBOARD--------------------------------------
            q_letter_button = Button(
                bottom_frame, text="Q", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"Q"))
            q_letter_button.grid(column=0, row=0, columnspan=2, sticky=W+E+N+S)
            w_letter_button = Button(
                bottom_frame, text="W", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"W"))
            w_letter_button.grid(column=2, row=0, columnspan=2, sticky=W+E+N+S)
            e_letter_button = Button(
                bottom_frame, text="E", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"E"))
            e_letter_button.grid(column=4, row=0, columnspan=2, sticky=W+E+N+S)
            r_letter_button = Button(
                bottom_frame, text="R", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"R"))
            r_letter_button.grid(column=6, row=0, columnspan=2, sticky=W+E+N+S)
            t_letter_button = Button(
                bottom_frame, text="T", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"T"))
            t_letter_button.grid(column=8, row=0, columnspan=2, sticky=W+E+N+S)
            y_letter_button = Button(
                bottom_frame, text="Y", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"Y"))
            y_letter_button.grid(column=10, row=0, columnspan=2, sticky=W+E+N+S)
            u_letter_button = Button(
                bottom_frame, text="U", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"U"))
            u_letter_button.grid(column=12, row=0, columnspan=2, sticky=W+E+N+S)
            i_letter_button = Button(
                bottom_frame, text="I", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"I"))
            i_letter_button.grid(column=14, row=0, columnspan=2, sticky=W+E+N+S)
            o_letter_button = Button(
                bottom_frame, text="O", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"O"))
            o_letter_button.grid(column=16, row=0, columnspan=2, sticky=W+E+N+S)
            p_letter_button = Button(
                bottom_frame, text="P", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"P"))
            p_letter_button.grid(column=18, row=0, columnspan=2, sticky=W+E+N+S)
            Num7_letter_button = Button(
                bottom_frame, text="*", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"*"))
            Num7_letter_button.grid(column=20, row=0, columnspan=2, sticky=W+E+N+S)
            Num8_letter_button = Button(
                bottom_frame, text="+", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"+"))
            Num8_letter_button.grid(column=22, row=0, columnspan=2, sticky=W+E+N+S)
            Num9_letter_button = Button(
                bottom_frame, text="@", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"@"))
            Num9_letter_button.grid(column=24, row=0, columnspan=2, sticky=W+E+N+S)
            
            
            #Middle of QWERTY KEYBOARD--------------------------------------
            a_letter_button = Button(
                bottom_frame, text="A", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"A"))
            a_letter_button.grid(column=1, row=1, columnspan=2, sticky=W+E+N+S)
            s_letter_button = Button(
                bottom_frame, text="S", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"S"))
            s_letter_button.grid(column=3, row=1, columnspan=2, sticky=W+E+N+S)
            d_letter_button = Button(
                bottom_frame, text="D", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"D"))
            d_letter_button.grid(column=5, row=1, columnspan=2, sticky=W+E+N+S)
            f_letter_button = Button(
                bottom_frame, text="F", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"F"))
            f_letter_button.grid(column=7, row=1, columnspan=2, sticky=W+E+N+S)
            g_letter_button = Button(
                bottom_frame, text="G", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"G"))
            g_letter_button.grid(column=9, row=1, columnspan=2, sticky=W+E+N+S)
            h_letter_button = Button(
                bottom_frame, text="H", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"H"))
            h_letter_button.grid(column=11, row=1, columnspan=2, sticky=W+E+N+S)
            j_letter_button = Button(
                bottom_frame, text="J", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"J"))
            j_letter_button.grid(column=13, row=1, columnspan=2, sticky=W+E+N+S)
            k_letter_button = Button(
                bottom_frame, text="K", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"K"))
            k_letter_button.grid(column=15, row=1, columnspan=2, sticky=W+E+N+S)
            l_letter_button = Button(
                bottom_frame, text="L", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"L"))
            l_letter_button.grid(column=17, row=1, columnspan=2, sticky=W+E+N+S)
            Num4_letter_button = Button(
                bottom_frame, text=".", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"."))
            Num4_letter_button.grid(column=20, row=1, columnspan=2, sticky=W+E+N+S)
            Num5_letter_button = Button(
                bottom_frame, text="/", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"/"))
            Num5_letter_button.grid(column=22, row=1, columnspan=2, sticky=W+E+N+S)
            Num6_letter_button = Button(
                bottom_frame, text="-", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"-"))
            Num6_letter_button.grid(column=24, row=1, columnspan=2, sticky=W+E+N+S)
            
            #Middle of QWERTY KEYBOARD--------------------------------------
            caps_letter_button = Button(
                bottom_frame, text=u'\u21e7', bg="#de6262", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.Caps(mainscreen))
            caps_letter_button.grid(column=0, row=2, columnspan=2, sticky=W+E+N+S)
            z_letter_button = Button(
                bottom_frame, text="Z", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"Z"))
            z_letter_button.grid(column=2, row=2, columnspan=2, sticky=W+E+N+S)
            x_letter_button = Button(
                bottom_frame, text="X", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"X"))
            x_letter_button.grid(column=4, row=2, columnspan=2, sticky=W+E+N+S)
            c_letter_button = Button(
                bottom_frame, text="C", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"C"))
            c_letter_button.grid(column=6, row=2, columnspan=2, sticky=W+E+N+S)
            v_letter_button = Button(
                bottom_frame, text="V", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"V"))
            v_letter_button.grid(column=8, row=2, columnspan=2, sticky=W+E+N+S)
            b_letter_button = Button(
                bottom_frame, text="B", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"B"))
            b_letter_button.grid(column=10, row=2, columnspan=2, sticky=W+E+N+S)
            n_letter_button = Button(
                bottom_frame, text="N", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"N"))
            n_letter_button.grid(column=12, row=2, columnspan=2, sticky=W+E+N+S)
            n_letter_button = Button(
                bottom_frame, text="M", bg="#6bcbd7", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"M"))
            n_letter_button.grid(column=14, row=2, columnspan=2, sticky=W+E+N+S)
            backspace_letter_button = Button(
                bottom_frame, text=u'\u21e6', bg="#de6262", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.remove_character_to_entry(mainscreen))
            backspace_letter_button.grid(column=16, row=2, columnspan=2, sticky=W+E+N+S)
            Num0_letter_button = Button(
                bottom_frame, text="!", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"!"))
            Num0_letter_button.grid(column=18, row=2, columnspan=2, sticky=W+E+N+S)
            Num1_letter_button = Button(
                bottom_frame, text="£", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"£"))
            Num1_letter_button.grid(column=20, row=2, columnspan=2, sticky=W+E+N+S)
            Num2_letter_button = Button(
                bottom_frame, text="$", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"$"))
            Num2_letter_button.grid(column=22, row=2, columnspan=2, sticky=W+E+N+S)
            Num3_letter_button = Button(
                bottom_frame, text="%", bg="#e7d2e5", font="Helvetica -20", fg="#04555f", bd=2, relief=RAISED, command=lambda: self.add_character_to_entry(mainscreen,"%"))
            Num3_letter_button.grid(column=24, row=2, columnspan=2, sticky=W+E+N+S)

    # Method for getting entry input and returning it to main order screen.
    def Add_customer_details_event(self):
        try:
            new_customer_number = self.var.get()
            print(new_customer_number)
            mainscreen.lookup_user_account_number = new_customer_number
            # mainscreen.threadcondition = 1          #added just in case, should not be the case
            mainscreen.threadcondition = 0         #changed to 0 to cancel QR Camera and restart polling if needed
            #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
            POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
            print("launching customer addition check frame2")       #Customer_addtion_check_frame2 is the version used to connect to bluehost
            self.destroy()
            Customer_addition_check_frame2(root)
        except TclError as err:         #add exception to avoid floating point number error. Ie when a blank number is tried adding as a customer number. pressing plus without entering any numbers
            print(err)
            # mainscreen.threadcondition = 1
            mainscreen.threadcondition = 0          #changed to 0 to cancel QR Camera and restart polling if needed
            #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
            POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
            print("launching customer error frame")
            self.destroy()
            Customer_error_frame(root)
        except AttributeError as err2:
            print("this is err2:", err2)
            # mainscreen.threadcondition = 1
            mainscreen.threadcondition = 0          #changed to 0 to cancel QR Camera and restart polling if needed
            #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
            POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
            print("launching customer error frame")
            self.destroy()
            Customer_error_frame(root)
        
    # Method to add values to  entry widget on add_customer_frame
    def add_character_to_entry(self, order_class, character):
        print("Old entry widget user number was: ", order_class.entry_widget_user_number)
        order_class.entry_widget_user_number = order_class.entry_widget_user_number + str(character)
        print("New entry widget user number is: ", order_class.entry_widget_user_number)
        customer_entry_widget.config(textvariable=self.var.set(mainscreen.entry_widget_user_number))
        customer_entry_widget.focus_set()
        
    def remove_character_to_entry(self, order_class):
        print("Old entry widget user number was: ", order_class.entry_widget_user_number)
        order_class.entry_widget_user_number = order_class.entry_widget_user_number[:-1] #slicing last character from string
        print("New entry widget user number is: ", order_class.entry_widget_user_number)
        customer_entry_widget.config(textvariable=self.var.set(mainscreen.entry_widget_user_number))
        customer_entry_widget.focus_set()
        
    # Threading the QR Code Reader
    def QR_Code_Read(self):
        POS_QR_Scanner.qr_scanning_on = True

    def Update_Frame(self):  # dataqueue is not capturing or not updating. Register_cups() method is always running and passing in polling method
        print("Frame trying to update")
        try:
            cupIDdata = dataQueue.get(block=False)
            print("CupIDdata is: ",cupIDdata)
        except queue.Empty:
            # Set at 250 which is same as Polling rate , currently stacking updates....
            self.after(250, self.Update_Frame)
            pass
        else:															# else is used to run code after successful try statement
            print("Frame has updated; closing customer_addition_frame and launching AppFrame")
            mainscreen.threadcondition = 0
            mainscreen.thread_qr_code = False
            self.destroy()
            AppFrame(root)
        

    def Cancel_add_customer_event(self, event):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
        POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
        mainscreen.entry_widget_user_number = ""
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        if mainscreen.user_account_number == 0:
            #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
            POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
            AppFrame(root)											# AppFrame(root) is the main window for no account on order
        else:
            # If an account is linked, mainscreen.user_account_number is not equal to zero, therefore it returns to the old screen where the account in use is still in use.
            SecondFrame(root)
            
    def Cancel_add_customer_event2(self):
        # Changing value to 0 allows polling to restart at next screen (Value of 1 pauses polling)
        mainscreen.threadcondition = 0
        #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
        POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
        mainscreen.entry_widget_user_number = ""
        self.destroy()
        # Mainscreen.user_account_number value of zero is a placeholder for no account linked to order currently
        if mainscreen.user_account_number == 0:
            #mainscreen.thread_qr_code = False          #Old QR code scanner method and threading class - new below
            POS_QR_Scanner.qr_scanning_on = False       #New QR code scanner class pausing on live data check with sever
            AppFrame(root)											# AppFrame(root) is the main window for no account on order
        else:
            # If an account is linked, mainscreen.user_account_number is not equal to zero, therefore it returns to the old screen where the account in use is still in use.
            SecondFrame(root)
    
    def Caps(self, order_class):
        customer_entry_widget.config(textvariable=self.var.set(mainscreen.entry_widget_user_number))
        customer_entry_widget.focus_set()
        mainscreen.threadcondition = 0
        mainscreen.thread_qr_code = False
        time.sleep(0.25)
        mainscreen.threadcondition = 1
        if order_class.switching_value == 1:
            order_class.switching_value = 0
        else:
            order_class.switching_value = 1
        self.destroy()
        Add_customer_frame(root)
        
    def Characters(self, order_class):
        customer_entry_widget.config(textvariable=self.var.set(mainscreen.entry_widget_user_number))
        customer_entry_widget.focus_set()
        mainscreen.threadcondition = 0
        mainscreen.thread_qr_code = False
        time.sleep(0.25)
        mainscreen.threadcondition = 1
        order_class.switching_value = 0
        self.destroy()
        Add_customer_frame(root)

class Customer_error_frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity

class Customer_addition_check_frame2(AppFrame):
    pass
    # Hidden function due to commericial sensitivity         


class Reset_order_frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity


class Remove_Cup_Frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity

class Paid_Frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity


class Order_Confirmation_Frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity

class Electronic_Processing_Frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity

class Refund_Cup_Frame(AppFrame):
    pass
    # Hidden function due to commericial sensitivity
            
class Refund_Confirmation_Page(AppFrame): 
    pass
    # Hidden function due to commericial sensitivity

class Admin_Options(AppFrame): 
    pass
    # Hidden function due to commericial sensitivity
        

class Admin_add_user_frame(Add_customer_frame): 
    pass
    # Hidden function due to commericial sensitivity
            
            
class Admin_Pin_Entry(AppFrame): 
    '''Standard Frame to be used on all admin confirmation requirements'''
    pass
    # Hidden function due to commericial sensitivity

class Super_Admin_Pin_Entry(Admin_Pin_Entry): 
    '''Frame to be used on super admin confirmation requirements'''
    pass
    # Hidden function due to commericial sensitivity
    
class Admin_change_user_pin_frame(Admin_Pin_Entry): 
    '''Frame to be used to double check new admin pin'''
    pass
    # Hidden function due to commericial sensitivity
                
class Admin_remove_user_selection_frame(Admin_Pin_Entry): 
    '''Standard Frame to be used on all admin confirmation requirements'''
    pass
    # Hidden function due to commericial sensitivity
    

class Cafe_Settings(AppFrame): 
    pass
    # Hidden function due to commericial sensitivity


class Cafe_Totals_Frame(AppFrame): 
    pass
    # Hidden function due to commericial sensitivity
        
class Report_errors_frame(AppFrame): 
    pass
    # Hidden function due to commericial sensitivity
        
              
class Report_error_confirmation_frame(AppFrame): 
    pass
    # Hidden function due to commericial sensitivity

if __name__ == '__main__':
    root = Tk()
    root.geometry('1024x600+0+0')
    root.title('App Window')
    #root.attributes('-type', 'dock') # Removes title bar, must use focus_force

    # must instigate after Tk called. Rest of resize can occur ealier in program
    beandrop_logo_new_size = ImageTk.PhotoImage(beandrop_logo_new_size)
    coffee_icon_new_crop = ImageTk.PhotoImage(coffee_icon_new_crop)
    coffee_bean_icon_new_size = ImageTk.PhotoImage(coffee_bean_icon_new_size)
    _thread.start_new_thread(hardware_status_update_timer,())
    _thread.start_new_thread(rfid_dictionary_updater,())

    AppFrame(root)
    root.mainloop()


