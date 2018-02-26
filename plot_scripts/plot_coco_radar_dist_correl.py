#Created on Fri Apr 4 12:32:17 2014
#@author: rspies
# Python 2.7
# This script reads the newly created Arogonne freeze/thaw file along with all of the
# paired COCORAHS ground-gage/nexrad data files
# Outputs a single double mass figure comparing mean gage to mean NEXRAD

import os
import datetime
from dateutil import parser
from scipy import stats
import matplotlib.pyplot as plt
plt.ioff()

criteria = 'Thaw' # choicea are 'Freeze' or 'Thaw' #see find_freeze_days.py for more info
gage_net = 'cocorahs'
padj = 1.14

os.chdir("..")
maindir = os.getcwd() + os.sep
################# create a list of days to use in the analysis ########################
ystart = 2007 # begin data grouping
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 2, 1, 0, 0)
finish = datetime.datetime(yend, 9, 30, 23, 0)

print 'Processing: ' + gage_net + ' gages...'
fstatus = open(maindir + '\\figures\\final\\status_files\\' + gage_net + '_stations_nexrad_correl_stats_' + str(ystart) + '_' + str(yend) + '.txt', 'w')
fstatus.write(str(start) + ' - ' + str(finish) + '\n')
fstatus.write('Station' + '\t' + 'Missing days in analysis\n')
print str(start) + ' - ' + str(finish)
################## Parse Argonne temperature file ################################    
# Loop through the Agronne temperature freeze criteria file previously generated
# Create a dictionary of dates for both the freeze and thaw criteria
print 'Examing:' + criteria + ' days...'
print 'Processing data for ' + 'Argonne hourly freeze/thaw data...'
fopen = open(maindir + 'data\\temperature\\argonne_freeze.txt','r')
temp_lib = {'Freeze': [], 'Thaw': []}
t_days = 0
for line in fopen:
    if line[:2] == '20': #ignores header
        udata = line.split('\t')
        date_check = parser.parse(udata[0])
        if date_check >= start and date_check <= finish:        
            temp = udata[1].rstrip()
            if temp == 'Thaw':
                temp_lib[temp].append(str(date_check))
            elif temp == 'Freeze':
                temp_lib[temp].append(str(date_check))
            else:
                print 'Error in Agronne freeze/thaw file: ' + date_check
            if temp == criteria:
                t_days += 1
fopen.close()
############# Search all gages info txt file  ####################
#### Also find station # for annotating points on plot
ftype = open(maindir + 'data\\INPUT_coco_cells_distance.txt','r')
gages_met = []
gages_nums = {}
radar_lib = {}
for every in ftype:
    if every[:4] != 'COCO':
        idinfo = every.split('\t')
        station_id = idinfo[3].rstrip()
        gage_num = idinfo[8].rstrip()
        gages_nums[str(station_id)] = str(gage_num)
        gages_met.append(station_id)
        ######### Search for radar distance ####################
        radar_dist = idinfo[10].rstrip()
        radar_lib[station_id]=float(radar_dist) 
      
###################### Search through paired gage/nexrad files  ####################    
# Loop through all paired Gage/NEXRAD files and create a dictionay of data
# for each data found in the paired files
print 'Searching through paired gage/nexrad data...'
gage_lib = {}; nex_lib = {}
pfiles = os.listdir(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\')    
for each_pair in pfiles:
    miss_cnt = 0
    if each_pair[:1] != 's' and each_pair[:-4] in gages_met: #ignores status.txt file
        popen = open(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\' + each_pair ,'r')
        print each_pair        
        for line in popen:
            if line[:2] == '20': #ignores header
                pdata = line.split('\t')
                date_check = str(parser.parse(pdata[0]))
                if date_check in temp_lib[criteria]:
                    pgage = pdata[1].rstrip()
                    pnex = pdata[2].rstrip()
                    if pgage != 'na' and pnex != 'na':
                        key = str(each_pair)[:-4]
                        if key in gage_lib:
                            gage_lib[key].append(float(pgage))
                        else:
                            gage_lib[key]=[float(pgage)]
                        if key in nex_lib:
                            nex_lib[key].append(float(pnex)*padj)
                        else:
                            nex_lib[key]=[float(pnex)*padj]
                    elif pgage == 'na':
                        miss_cnt += 1 # tally missing ('na') instances at the gage                                                
        popen.close()
        fstatus.write(each_pair[:-4] + '\t' + str(miss_cnt) + '\n')
fstatus.close()
    
###################### Only use Freeze or Thaw days  ####################        
# Finally search for gage/nexrad data on the days where the freeze criteria is
# acceptable and create a list of accumulated gage data and a list of accumulated
# nexrad data for plotting
in_gage = []
ratio_lib = {}
gage_accum = 0; nex_accum = 0; total_days = 0
for station in gage_lib:
    if len(gage_lib[station]) == len(nex_lib[station]):
        total_gage = sum(gage_lib[station])
        total_nex = sum(nex_lib[station])
        in_gage.append(((total_nex - total_gage)/total_gage)*100)
        ratio_lib[station]=(((total_nex - total_gage)/total_gage)*100)
    else:
        print 'Error!! Gage and NEXRAD records different lengths'

###################### Create Figure ########################################          
print 'Creating figure...'
fig = plt.figure()
ax1 = fig.add_subplot(111)
cnt = 0; x = []; y = [] #copy x and y variables to list -> use for linear fit below
for stations in gages_met:
    if cnt == 0:
        ax1.plot(radar_lib[stations], ratio_lib[stations], 'o', color = 'green', markersize = 9, label = str(len(gages_met)) + ' locations')
    else:
        ax1.plot(radar_lib[stations], ratio_lib[stations], 'o', color = 'green', markersize = 9)
    #ax1.annotate(gages_nums[stations], xy=(radar_lib[stations], ratio_lib[stations]),
    #             xycoords='data',xytext=(5, 5), textcoords='offset points')
    x.append(radar_lib[stations])
    y.append(ratio_lib[stations])
    cnt += 1
####################### Add a trend line and r^2 to the plot #################
#slope, intercept = numpy.polyfit(x, y, 1)
#cc = numpy.corrcoef(y,line_fit)
#value = str(cc[1])
#cc1 = round(float(value[2:7]),2)
#r2 = cc1**2
slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)    
print 'slope: ' + str(slope)
print 'intercept: ' + str(intercept)
print 'r_value: ' + str(r_value)
print 'p_value: ' + str(p_value)
print 'std_err: ' + str(std_err)
line_fit = []
for xx in x:
    line_fit.append(intercept + (slope * xx))
r2 = r_value**2
if intercept > 0:
    eq = 'y = ' + str("%.3f" % slope) + 'x + ' + str("%.3f" % intercept)
else:
    eq = 'y = ' + str("%.3f" % slope) + 'x - ' + str("%.3f" % abs(intercept))
ax1.plot(x, line_fit, color='red', linestyle='-', label = eq +'\n' + r'$R^2$ = ' + str("%.2f" % r2) + '\n' + r'$p$' + '-value = ' + str("%.4f" % p_value))

##################### Add labels and Gridlines ##################################
plt.rcParams['axes.unicode_minus'] = False  # change axis tick label negative signs to normal hyphen (default is long hyphen? - USGS format request)
if padj != 1.0:
    ax1.set_ylabel('((Total adjusted NEXRAD'+ u"\u2013" +'MPE - total CoCoRaHS gage)/\ntotal CoCoRaHS gage) x 100', fontsize=10)
else:
    ax1.set_ylabel('((Total NEXRAD'+ u"\u2013" +'MPE - total CoCoRaHS gage)/\ntotal CoCoRaHS gage) x 100', fontsize=10)
ax1.set_xlabel('Distance from radar KLOT (miles)')
if criteria == 'Thaw':
    text = 'Nonfreezing days'
if criteria == 'Freeze':
    text = 'Freezing days'
#ax1.set_title('Gage-Radar Distance Correlation\n' + 'CoCoRaHS Gages, ' + text + ': ' + str(start.month) +'/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) +'/' + str(finish.day) + '/' + str(finish.year)) 
ax1.set_title(text + ', ' + str(start.month) +'/' + str(start.day) + '/' + str(start.year) + u"\u2013" + str(finish.month) +'/' + str(finish.day) + '/' + str(finish.year)) 
ax1.grid(True)
ax1.legend(loc='lower right',numpoints = 1)

plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + gage_net + '_gages\\' + 'gage_radar_dist_correl_' + criteria + '_days_padj.png', dpi=150, bbox_inches='tight')
#close('all') #closes all figure windows    
print 'Complete!'