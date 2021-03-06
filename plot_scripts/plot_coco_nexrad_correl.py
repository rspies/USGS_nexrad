#Created on Fri April 4 11:53:17 2014
#@author: rspies
# Python 2.7
# This script reads the newly created Arogonne freeze/thaw file along with all of the
# paired COCORAHS ground-gage/nexrad data files
# Outputs a single pointwise total plot comparing totoal precip for each gage agains corresponding NEXRAD cell value

import os
import datetime
from dateutil import parser
import numpy
import matplotlib
import matplotlib.pyplot as plt
import calc_errors
plt.ioff()
os.chdir("..")
maindir = os.getcwd() + os.sep

criteria = 'Thaw' # choicea are 'Freeze' or 'Thaw' #see find_freeze_days.py for more info
gage_net = 'cocorahs'
point_labels = 'no' # choices: 'yes', 'no' #plot point number labels
padj = 1.14

################# create a list of days to use in the analysis ########################
ystart = 2007 # begin data grouping
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 2, 1, 0, 0)
finish = datetime.datetime(yend, 9, 30, 23, 0)

fstatus = open(maindir + '\\figures\\final\\status_files\\' + gage_net + '_' + criteria + '_stations_stats_' + str(ystart) + '_' + str(yend) + '.txt', 'w')
fstatus.write(str(start) + ' - ' + str(finish) + '\n')
fstatus.write('Station' + '\t' + 'Missing days in analysis\n')
print str(start) + ' - ' + str(finish)
################## Parse Argonne temperature file ################################    
# Loop through the Agronne temperature freeze criteria file previously generated
# Create a dictionary of dates for both the freeze and thaw criteria
print 'Examing:' + criteria + ' days and ' + gage_net + ' gages...'
print 'Processing data for ' + 'Argonne hourly freeze/thaw data...'
fopen = open(maindir + 'data\\temperature\\argonne_freeze_7a_7a.txt','r')
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
############# Search through all gages in info txt file  ####################
#### Also find station # for annotating points on plot
ftype = open(maindir + 'data\\INPUT_coco_cells_distance.txt','r')
gages_met = []
gages_nums = {}
for every in ftype:
    if every[:4] != 'COCO':
        idinfo = every.split('\t')
        station_id = idinfo[3].rstrip()
        gage_num = idinfo[8].rstrip()
        gages_nums[str(station_id)] = str(gage_num)
        gages_met.append(station_id)

###################### Search through paired gage/nexrad files  ####################    
# Loop through all paired Gage/NEXRAD files and create a dictionay of data
# for each data found in the paired files
print 'Searching through paired gage/nexrad data...'
gage_lib = {}
nex_lib = {}
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
                        key = str(each_pair)
                        if key in gage_lib:
                            gage_lib[key].append(float(pgage))
                        else:
                            gage_lib[key]=[float(pgage)]
                        if key in nex_lib:
                            nex_lib[key].append(float(pnex))
                        else:
                            nex_lib[key]=[float(pnex)]
                    elif pgage == 'na':
                        miss_cnt += 1 # tally missing ('na') instances at the gage                                                
        popen.close()
        fstatus.write(each_pair[:-4] + '\t' + str(miss_cnt) + '\n')
fstatus.close()
    
###################### Only use Freeze or Thaw days  ####################        
# Finally search for gage/nexrad data on the days where the freeze criteria is
# acceptable and create a list of accumulated gage data and a list of accumulated
# nexrad data for plotting
print 'Creating figure...'
in_gage = []
gage_accum = 0
in_nex = []
nex_accum = 0
total_days = 0
for station in gage_lib:
    if len(gage_lib[station]) == len(nex_lib[station]):
        total_gage = sum(gage_lib[station])
        total_nex = sum(nex_lib[station]) * padj
        in_gage.append(total_gage)
        in_nex.append(total_nex)
    else:
        print 'Error!! Gage and NEXRAD records different lengths'
        
############################## Create Figure ####################################       
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.plot(in_gage[1], in_nex[1], 'o', linestyle='None', color='green', markersize = 9, label = str(len(in_gage))+' locations')#plot 1st point twice -- for legend label
ax1.plot(in_gage, in_nex, 'o', color='green', markersize = 9)
if max(in_gage) > max(in_nex):
    maximum = max(in_gage)
else:
    maximum = max(in_nex)
if min(in_gage) < min(in_nex):
    minimum = min(in_gage)
else:
    minimum = min(in_nex)
ax1.plot(range(int(maximum)+50), color = 'k', label = '1:1') # adds a 1:1 line for reference
if minimum > 20:
    ax1.set_ylim([minimum - 20,maximum + 10])
    ax1.set_xlim([minimum - 20,maximum + 10])
else:
    ax1.set_ylim([0,maximum + 10])
    ax1.set_xlim([0,maximum + 10])
    
################### Calculate Error Statistics and add to plot ################
pbias, mae, ns = calc_errors.print_errors(in_gage,in_nex)
textstr = '\nMean percent difference:\n' + r'$\frac{1}{n}\sum_{i=1}^n\frac{(y_i-x_i)}{x_i}$ = ' + str('%.1f' % pbias) +' percent\n\n' + 'Mean absolute difference:\n ' + r'$\frac{1}{n}\sum_{i=1}^n\vert y_i - x_i\vert$ = '+ str('%.2f' % mae) + ' inches'  #Mean Absolute Difference
varstr = '$\it{n}$'+': number of points\n' + '$\it{i}$'+': the point index\n' + '${y_i}$'+': the y-axis value of the $i^{th}$ point\n' + '${x_i}$'+': the x-axis value of the $i^{th}$ point'

#textstr = 'Mean Percent Difference = ' + str('%.1f' % pbias) +'%\n' + 'Mean Absolute Difference = ' + str('%.2f' % mae) + ' in'
# these are matplotlib.patch.Patch properties
props = dict(boxstyle='round', facecolor = '0.8', alpha=0.5)

# place a text box in upper left in axes coords
ax1.text(0.03, 0.97, textstr, transform=ax1.transAxes, fontsize=12.5,
        verticalalignment='top', bbox=props)
# place a text box in lower left in axes coords
ax1.text(0.57, 0.19, varstr, transform=ax1.transAxes, fontsize=10.5,
        verticalalignment='top', bbox=props)

###### OPTION: annotate site number labels without overlapping
if point_labels == 'yes':
    import my_plot_module
    my_plot_module.annotates_number(gage_lib,in_gage,in_nex,ax1,gages_nums)

##################### Add labels and Gridlines ##################################
ax1.set_xlabel('Total CoCoRaHS gage precipitation (inches)')
if padj > 1.0:
    ax1.set_ylabel('Total adjusted NEXRAD'+ u"\u2013" +'MPE precipitation (inches)')
else:
    ax1.set_ylabel('Total NEXRAD'+ u"\u2013" +'MPE precipitation (inches)')
if criteria == 'Thaw':
    text = 'Nonfreezing days'
if criteria == 'Freeze':
    text = 'Freezing days'
#ax1.set_title('Pointwise Total of Gages and Overlying NEXRAD cells\n' + 'CoCoRaHS Gages, ' + text + ': ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + ' - ' + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year))
ax1.set_title(text + ', ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + u"\u2013" + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year))
ax1.grid(True)
ax1.legend(bbox_to_anchor=(1.0, 0.37),numpoints = 1)

if padj <= 1.0:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + gage_net + '_gages\\' + 'station_correlation_' + criteria + '_days_' + str(ystart) + '.png', dpi=150, bbox_inches='tight')
else:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + gage_net + '_gages\\' + 'station_correlation_' + criteria + '_days_' + str(padj) + '_' + str(ystart) + '.png', dpi=150, bbox_inches='tight')

#close('all') #closes all figure windows    
print 'Complete!'