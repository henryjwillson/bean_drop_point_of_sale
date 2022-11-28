# Local Database Class
# SQLite3 database class for Point of Sale
import sqlite3 #Importing SQLite
from collections.abc import Mapping

class POS_local_db_class:
	'''This class defines the methods and operations involved with storing orders in the local database.
	The localised database generated is a simplified version of the main database'''
	
	def __init__(self, database_name):
		self.database_name = database_name
	
	def create_ldb(self):
		'''This method creates the new database and inserts the two relavent new tables.'''
	
	def insert_new_order(self, variables, screen_class, cups_dictionary, cafe_class):
		'''This method inserts a new order into the local database on the individual point of sale.
		Values and variables are taken from values after submission to the global database'''
		
	def return_order_rfid_numbers(self,variables):
		'''variables are: order_id_POS_ldb (sequential automatically generated number)'''

		
	def return_historic_order_ldb(self, variables):
		'''variables are: order_id_POS_ldb (sequential automatically generated number)'''
		
	
	def return_historic_order_from_offset_ldb(self, offset):
		'''This function returns the last order id used in the local database. This allows offset class to populate id numbers for the old orders screen'''
		
		
	def return_historic_orders_in_time_period(self):
		'''This function is designed to identify cups this point of sale has sold in the last hour, this updates a dictionary which rfid's are checked against when scanned in;
		this is to warn staff of duplicate selling of cups'''
		
		
	def issue_order_refund(self):
		'''This function updates an old order to determine it was refunded, generates a new refund_order_history and updates cup ownership database'''
		pass


class offset_numbers_class:
	'''This class represents a global method of updating offset numbers'''

	def __init__(self, first_offset, second_offset, third_offset, fourth_offset, fith_offset, selected_offset):
		self.first_offset = first_offset
		self.second_offset = second_offset
		self.third_offset = third_offset
		self.fourth_offset = fourth_offset
		self.fith_offset = fith_offset
		self.selected_offset = selected_offset
		
	def add_to_offset(self):
		self.first_offset += 5
		self.second_offset += 5
		self.third_offset += 5
		self.fourth_offset += 5
		self.fith_offset += 5
		print(self.fith_offset)
		
	def minus_from_offset(self):
		if self.first_offset == 0:
			print("Not possible to reduce offset anymore")
			pass
		else:
			self.first_offset -= 5
			self.second_offset -= 5
			self.third_offset -= 5
			self.fourth_offset -= 5
			self.fith_offset -= 5
			print(self.fith_offset)
			
	def reset_offset(self):
		self.first_offset = 0
		self.second_offset = 1
		self.third_offset = 2
		self.fourth_offset = 3
		self.fith_offset = 4
	
	def __str__(self):
		return 'first_offset: %s , second_offset: %s, third_offset: %s, fourth_offset: %s, fith_offset: %s' % (self.first_offset, self.second_offset, self.third_offset, self.fourth_offset, self.fith_offset)

class offset_order_class:
	'''This is a simplified class of the screen numbers class; this class only contains information relavent to the old orders and removes any information related to the POS
	This class is used to populate 5 members of the class directly related to the offset numbers; this is then used to populate the old orders screen'''
	
	def __init__(self, order_id_POS_ldb, order_id_overall_ldb, order_datetime, user_unique_ID_ldb, pos_hash_id_ldb, cups_registered_ldb, value_taken_ldb, order_value_ldb):
		self.order_id_POS_ldb = order_id_POS_ldb
		self.order_id_overall_ldb = order_id_overall_ldb
		self.order_datetime = order_datetime
		self.user_unique_ID_ldb = user_unique_ID_ldb
		self.pos_hash_id_ldb = pos_hash_id_ldb
		self.cups_registered_ldb = cups_registered_ldb
		self.value_taken_ldb = value_taken_ldb
		self.order_value_ldb = order_value_ldb
	
	@property
	def new_cups_calculated(self):
		return self.value_taken_ldb // 3  #double division sign returns a result with no remainder
		
	@property
	def account_cups_calculated(self):
		return self.cups_registered_ldb - self.new_cups_calculated	#double division sign returns a result with no remainder
	
	def update_offset_order_class(self, variables):
		self.order_id_POS_ldb = variables[0]
		self.order_id_overall_ldb = variables[1]
		self.order_datetime = variables[2]
		self.user_unique_ID_ldb = variables[3]
		self.pos_hash_id_ldb = variables[4]
		self.cups_registered_ldb = variables[5]
		self.value_taken_ldb = variables[6]
		self.order_value_ldb = variables[7]
	
	def reset(self):
		self.order_id_POS_ldb = ""
		self.order_id_overall_ldb = ""
		self.order_datetime = ""
		self.user_unique_ID_ldb = ""
		self.pos_hash_id_ldb = ""
		self.cups_registered_ldb = 0
		self.value_taken_ldb = 0
		self.order_value_ldb = 0
		
	def __str__(self):
		return 'order_id_POS_ldb: %s , order_id_overall_ldb: %s , order_datetime: %s , user_unique_ID_ldb: %s , pos_hash_id_ldb: %s , cups_registered_ldb: %s , value_taken_ldb: %s , order_value_ldb: %s' % (self.order_id_POS_ldb, self.order_id_overall_ldb, self.order_datetime, self.user_unique_ID_ldb, self.pos_hash_id_ldb, self.cups_registered_ldb, self.value_taken_ldb, self.order_value_ldb)

# Utility function to perform task
def total_keys_new_method(test_dict):
    for key, value in test_dict.items():
        if isinstance(value, Mapping):
            yield from total_keys_new_method(value)
    yield len(test_dict)	
    

if __name__ == '__main__':
	#Internal Testing Here:
	import time
	
