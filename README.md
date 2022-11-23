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
- Hardware and sotware restart.

## Python Libraries used
- Pillow
- 

*Note: The Bean Drop 'Point of Sale Attachment' is not a True Point of Sale as it does not process any payments directly (card or cash), however it succurely updates user accounts in the Bean Drop database which contain 'cup deposits' 
Bean Drop Point of Sale attachment software. Interactive GUI for café staff interacting with; rfid scanner, qr-code scanner, google cloud mysql database, thermal printer
