# Bean Drop Point of Sale
The Bean Drop 'Point of Sale Attachment' is a hardware unit supplied to cafes operating in the Bean Drop community. It allows cafe staff to scan in Bean Drop Cups using an rfid scanner, link customer accounts using a qr-code scanner, print receipts using a thermal printer and links purchases to the main Bean Drop database based securely on the google cloud using SSL connections.

Full video demo's of operation can be found here:
#
This unit is running on a varient of Debian Linux. The hardware involved is a custom pcb board, a small single board computer, a thermal printer, a camera module and a rfid scanner module. 


## Functions in the Point of Sale
- Scan Bean Drop Cups using RFID scanner.
- Scan Customer qr-code linked accounts (manual addition of accounts with touch keyboard also possible).
- Admin Passcode security.
- Admin staff user account setup and removal. This provides each staff member with a unique account linked to all orders / actions.
- Printing Thermal Receipts for customer orders. Receipts can be printed for old orders using the historical orders table.
- Connection to SSL database in Google Cloud to process customer orders and point of sale attachment actions.
- Encrypted new user account generation.
- Localised database for backups.
- Historic order table
- Refund processing
- Hardware status and database connection monitoring
- Hardware and sotware restart.

## Python Libraries used
- PIL
- tkinter
- time
- math
- multiprocessing
- RPi.GPIO
- subprocess
- os 
- traceback 
- _thread
- queue
- sqlite3
- datetime
- collections.abc (Mapping)
- mysql.connector
- csv
- serial
- smbus
- sys
- qrcode

# Hidden Code and Functions
As a commercial product, a number of code sections have been removed to protect Bean Drop Ltd's product. The hidden sections are listed below along with links to operational demos of the hidden sections functionality.
- Thermal Printer Receipt Printing
- Encryption and new user account generation
- Hardware status and database connection monitoring
- Connect_functions.py has a significant number of functions removed/hidden as part of commercial security as they access the Bean Drop production database.

*Note: The Bean Drop 'Point of Sale Attachment' is not a True Point of Sale as it does not process any payments directly (card or cash), however it succurely updates user accounts in the Bean Drop database which contain 'cup deposits' 
Bean Drop Point of Sale attachment software. Interactive GUI for café staff interacting with; rfid scanner, qr-code scanner, google cloud mysql database, thermal printer
