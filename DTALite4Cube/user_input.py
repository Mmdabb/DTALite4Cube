import pandas as pd

# START OF ARGUMENTS

# Network directory
net_dir = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\yaml'

# Assignment argument
iteration = 1
route = 1
simu = 0
UE_converge = 0.1

# Units arguement
length = 'meter'
speed = 'mph'

# Demand period arguement
period_title = ['am','md','pm','nt']
period_time = ['0800_0900','1100_1200','1600_1700','2100_2200']

# Mode type argument
modes = ['apv','com','hov2','hov3','sov','trk']
modes_dedicated = [1,0,0,0,1,0]
modes_person = [1,1,2,3,1,1]

# Demand scale factor
demand_scale_factor = 1

# END OF ARGUMENTS


# Demand file generation based on mode type and demand period
demand_file = []
demand_mode = []
demand_title = []
for mode in modes:
    for title in period_title:
        demand_mode.append(mode)
        demand_title.append(title)
        demand_file.append(mode + '_' + title + '.csv')
        
# Scenario generation based on demand period
scenario_gen = []
for title in period_title:
    scenario_gen.append('scenario_' + title)

# Link type generation
df = pd.read_csv('link_type_NVTA.csv')

