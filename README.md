# Bean Drop Point of Sale
The Bean Drop 'Point of Sale Attachment' is a hardware unit supplied to cafes operating in the Bean Drop community. It allows cafe staff to scan in Bean Drop Cups using an rfid scanner, link customer accounts using a qr-code scanner, print receipts using a thermal printer and links purchases to the main Bean Drop database based securely on the google cloud using SSL connections.

Full video demo's of operation can be found here:
#
This unit is running on a varient of Debian Linux. The hardware involved is a custom pcb board, a small single board computer, a thermal printer, a camera module and a rfid scanner module. 

The main file to run is named: 'POS_GUI_Rev1_8T_MySQL.py'. This is normally executed by an executable file deployed outside of the project folders. All other files supliment and help run 'POS_GUI_Rev1_8T_MySQL.py'.


## Functions in the Point of Sale
- Scan Bean Drop Cups using RFID scanner.
- Scan Customer qr-code linked accounts (manual addition of accounts with touch keyboard also possible).
- Admin Passcode security.
- Admin staff user account setup and removal. This provides each staff member with a unique account linked to all orders / actions.
- Printing Thermal Receipts for customer orders. Receipts can be printed for old orders using the historical orders table.
- Encrypted new user account generation.
- Connection to SSL database in Google Cloud to process customer orders and point of sale attachment actions.
- Localised database for backups.
- Order processing
- Cup transfers and auto ownership correction
- Historic order table
- Refund processing
- Hardware status and database connection monitoring
- Hardware and sotware restart.
- Error management and processing

## Python Libraries used

- argparse
- collections.abc
- csv
- cv2
- datetime
- math
- multiprocessing
- mysql.connector
- os
- passlib.context
- PIL
- pyzbar
- qrcode
- queue
- RPi.GPIO
- serial
- smbus
- sqlite3
- subprocess
- sys
- _thread
- time
- tkinter
- traceback

# Hidden Code and Functions
As a commercial product, a number of code sections have been removed to protect Bean Drop Ltd's product. The hidden sections are listed below along with links to operational demos of the hidden sections functionality.
- Encryption and new user account generation
- Hardware status and database connection monitoring
- Connect_functions.py has a significant number of functions removed/hidden as part of commercial security as they access the Bean Drop production database.
- Significant number of class based tkinter Frames from 'POS_GUI_Rev1_8T_MySQL.py' have also been removed / hidden. A number of Example frames have already been provided and represent the same quality of code in the hidden frames. These hidden frames are shown to be operational here: 

*Note: The Bean Drop 'Point of Sale Attachment' is not a True Point of Sale as it does not process any payments directly (card or cash), however it succurely updates user accounts in the Bean Drop database which contain 'cup deposits' 
Bean Drop Point of Sale attachment software. Interactive GUI for café staff interacting with; rfid scanner, qr-code scanner, google cloud mysql database, thermal printer
