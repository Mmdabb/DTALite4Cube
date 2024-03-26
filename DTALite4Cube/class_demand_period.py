from user_input import period_title, period_time

demand_periods = []

# Define the demand periods as dictionaries
for i in range(len(period_title)):
    demand_period = {
        'demand_period': period_title[i],
        'demand_period_id': i+1,
        'time_period': period_time[i]    
    }
    
    # Append the demand periods into a demand periods list
    demand_periods.append(demand_period)

# Add the demand periods list to the demand period dictionary 
demand_period_dict = {'demand_periods': demand_periods}

