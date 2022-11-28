class cafe_totals_return_class:
    '''This class represents the numbers on the mainscreen GUI'''

    def __init__(self, cup_total, deposit_total, deposit_value, time_period):
        self.cup_total = cup_total
        self.deposit_total = deposit_total
        self.deposit_value = deposit_value
        self.time_period = time_period
        
cafe_today = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 1)
cafe_7_days = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 7)
cafe_30_days = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 30)
cafe_365_days = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 365)
cafe_last_week = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 0)
cafe_last_month = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 0)
cafe_last_year = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 0)
cafe_variable_time = cafe_totals_return_class("UPDATING", "UPDATING", "UPDATING", 0)

