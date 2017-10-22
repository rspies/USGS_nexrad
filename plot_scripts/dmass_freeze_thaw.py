#Created on Fri March 24 08:37:17 2014
#@author: rspies
# Python 2.7
# This script reads the newly created Arogonne freeze/thaw file along with all of the
# paired ground-gage/nexrad data files
# Outputs a single double mass figure comparing mean gage to mean NEXRAD

import os
import datetime
from dateutil import parser
import numpy
import matplotlib.pyplot as plt
import my_plot_module
import module_parse_txt

os.chdir("../..")
maindir = os.getcwd() + os.sep
criteria = 'Freeze' # choices: 'Freeze', 'Thaw'
netx = 'usgs' # choices: 'usgs', 'cocorahs'
nety = 'cocorahs' # choices: 'nexrad', 'cocorahs'

###### NEXRAD and USGS gages are adjusted in current HSPF application #######
nexadj = gadj = 1.14 # 1.14
if netx == 'cocorahs': # don't adjust cocorahs data
    gadj = 1.0
if netx == 'usgs' and nety == 'cocorahs': # don't apply adj to nety when compring usgs to cocorahs
    nexadj = 1.0
##### Snow Correction Factor (usgs gages only) #####
if criteria == 'Freeze' and netx == 'usgs':
    scf = 1.0
else:
    scf = 1.0
    
################# create a list of days to use in the analysis ########################
ystart = 2007 # begin data grouping -- good coco data starts 2007!!!
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 2, 1, 0, 0)
finish = datetime.datetime(yend, 9, 30, 23, 0)
if netx == 'usgs' and nety == 'nexrad':
    ystart = 2002
    start = datetime.datetime(ystart, 2, 1, 0, 0)
print 'Time Period: ' + str(start) + ' - ' + str(finish)

################## Parse Argonne temperature file ################################    
# Loop through the Agronne temperature freeze criteria file previously generated
# Create a dictionary of dates for both the freeze and thaw criteria
if nety == 'nexrad':
    fstatus = open(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + netx 
+ '_gages' + '\\status_dmass_' + criteria + '_' + netx + '_' + str(ystart)[-2:] + '_' + str(yend)[-2:] + '.txt', 'w')
else:
    fstatus = open(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + netx 
+ '_vs_' + nety + '\\status_dmass_' + criteria + '_' + str(ystart)[-2:] + '_' + str(yend)[-2:] + '.txt', 'w')


print 'Examing:' + criteria + ' days...'
print 'Processing data for ' + 'Argonne hourly freeze/thaw data...'
if netx == 'cocorahs':
    fopen = open(maindir + 'data\\temperature\\argonne_freeze_7a_7a.txt','r')
else:
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
                print 'Error in Agronne freeze/thaw file: ' + str(date_check)
            if temp == criteria:
                t_days += 1
fopen.close()
############# Search through heated, unheated, or all gages in info txt files  ####################
gages_met1,gages_met2 = module_parse_txt.find_gages(maindir,criteria,netx,nety)
print gages_met1
### set the minimum num of gages required for analysis below
#req_gages = int(numpy.ceil(float(len(gages_met))/5)) 
if netx == 'usgs' and criteria == 'Freeze':
    req_gages = 4
else:
    req_gages = 10

###################### Search through paired gage/nexrad files  ####################    
# Loop through all paired Gage/NEXRAD files and create a dictionay of data
# for each data found in the paired files
print 'Searching through paired gage/nexrad data...'
x_lib = {}; y_lib = {}
module_parse_txt.get_gage_data(maindir,netx,nety,start,finish,gages_met1,gages_met2,gadj,nexadj,scf,x_lib,y_lib)

###################### Only use Freeze or Thaw days  ####################        
# Finally search for gage/nexrad data on the days where the freeze criteria is
# acceptable and create a list of accumulated gage data and a list of accumulated
# nexrad data for plotting
print 'Creating figure...'
in_gage = []
gage_accum = 0
in_nex = []
nex_accum = 0
date_plot = [] # available date list to reference for annotating points below
total_days = 0
missing = 0
availables = []
for days in temp_lib[criteria]:
    if days in x_lib and days in y_lib:
        if len(x_lib[days]) >= req_gages and len(y_lib[days]) >= req_gages:
            mean_gage = numpy.mean(x_lib[days])
            gage_accum += mean_gage
            mean_nex = numpy.mean(y_lib[days])
            nex_accum += mean_nex
            in_gage.append(gage_accum)
            in_nex.append(nex_accum)
            total_days += 1
            date_plot.append(days)
            #availables.append(round((float(len(x_lib[days]))/len(gages_met1)*100),0))
            availables.append(int(len(x_lib[days])))
            #print str(len(x_lib[days])) + ' -- ' + str(len(gages_met1))
        else:
            print 'Ignoring day -> not enough station/cell data (need ' + str(req_gages) + '): ' + str(days)
            missing += 1
    else:
        print 'Ignoring day (missing): ' + str(days)
        missing += 1
##### print and write analysis results ##########################        
print str(start) + ' - ' + str(finish)
print 'Days meeting freeze/thaw category: ' + str(t_days)
print 'Total of those days with available gage/nexrad data: ' + str(total_days)
print 'Missing days: ' + str(missing)
fstatus.write(str(start) + ' - ' + str(finish) + '\n')
fstatus.write('Analyzing: ' + str(len(gages_met1)) + ' stations'+ '\n')
fstatus.write('Required number of gages each day set to: ' + str(req_gages)+ '\n')
fstatus.write('Days meeting freeze/thaw category: ' + str(t_days)+ '\n')
fstatus.write('Total of those days with available gage/nexrad data: ' + str(total_days)+ '\n')
fstatus.write('Missing days: ' + str(missing)) 

################# Finally - Create double mass figure ######################### 
###### Find the proper gage network name ##########
if netx == 'cocorahs':
    netx_name = 'CoCoRaHS'
else:
    netx_name = netx.upper()
if nety == 'cocorahs':
    nety_name = 'CoCoRaHS'
else:
    nety_name = nety.upper()   
      
fig = plt.figure()
ax1 = fig.add_subplot(111) # '#9F000F'
ax1.plot(in_gage, in_nex, color = 'k', ls='--', dashes=(2,2), lw =1.75, label = 'Double Mass')

######## option: add color coded scatter plot with gage availability value #####
label = 'Number of Available ' + netx_name + ' Gages'
my_plot_module.colormap(fig,ax1,in_gage,in_nex,availables,label)

######## calculate max/min values for use on x/y axes #########################
x = in_gage; y = in_nex
maximum = my_plot_module.axis_limits(x,y,ax1)

################ add 1:1 line for reference ##################################
ax1.plot(range(int(maximum)), color = 'k', label = '1:1') # adds a 1:1 line for reference

##################### option: label intervals on accumulation line ####################
x = in_gage; y = in_nex
my_plot_module.annotate_dates(criteria,ystart,finish,date_plot,x,y,ax1)

##################### option: add number of days in analysis text box #################
textstr = 'Days in Analysis = ' + str('%i' % total_days)
# these are matplotlib.patch.Patch properties
props = dict(boxstyle='round', facecolor = '0.8', alpha=0.5)

# place a text box in upper left in axes coords
ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

##################### Add labels and Gridlines ##################################
######## Label axes with appropriate precip and adjustments #######
if nety == 'nexrad':
    if nexadj > 1.0:
        ax1.set_ylabel('Cumulative Average of Adjusted NEXRAD-MPE (inches)')
    else:
        ax1.set_ylabel('Cumulative Average of NEXRAD-MPE (inches)')
else:
    if nexadj > 1.0:
        ax1.set_ylabel('Cumulative Average of Adjusted\n' + nety_name + ' Gage Precipitation (inches)')
    else:
        ax1.set_ylabel('Cumulative Average of\n' + nety_name + ' Gage Precipitation (inches)')
if gadj > 1.0:
    ax1.set_xlabel('Cumulative Average of Adjusted\n' + netx_name + ' Gage Precipitation (inches)')
else:
    ax1.set_xlabel('Cumulative Average of\n' + netx_name + ' Gage Precipitation (inches)')
######### Add Title ###########
title_text = ''
if nety == 'nexrad':
    title_text+=(netx.upper() + ' Gages,')
else:
    if netx == 'usgs' and criteria == 'Freeze':
        title_text+= 'Heated '
    title_text+=(netx.upper() + ' and ' + nety.upper() + ' Gages\n')

if criteria == 'Thaw':
    plt.title('Double Mass Analysis of Cumulative Averages\n' + title_text +' Non-freezing Days: ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + ' - ' + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year),fontsize='13',y=1.006) #\n' + str(start)[:10] + ' -- ' + str(finish)[:10]  + ' (' + str(len(in_gage)) + ' days)')
if criteria == 'Freeze':
    plt.title('Double Mass Analysis of Cumulative Averages\n' + title_text +' Freeze Days: ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + ' - ' + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year),fontsize='13',y=1.006) # + str(start)[:10] + ' -- ' + str(finish)[:10] + ' (' + str(len(in_gage)) + ' days)')
ax1.grid(True)
ax1.legend(loc='lower right',numpoints = 1)

#################### Save figure with adj value in name #####################
if nety == 'nexrad':
    netx = netx + '_gages'
else:
    netx = netx + '_vs_' + nety
if nexadj == 1.0 and gadj == 1.0:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + netx + '\\double_mass_' +str(ystart) +'_'+str(yend) + '.png', dpi=150, bbox_inches='tight')
elif nexadj > 1.0:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + netx + '\\double_mass_' +str(ystart) +'_'+str(yend) + '_adj_' + str(nexadj) +'.png', dpi=150, bbox_inches='tight')
else:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\' + netx + '\\double_mass_' +str(ystart) +'_'+str(yend) + '_adj_' + str(gadj) +'.png', dpi=150, bbox_inches='tight')

############# Calculate difference statistics #####################
pdiff = ((in_gage[-1]-in_nex[-1])/in_gage[-1])*100
absdiff = abs(in_gage[-1]-in_nex[-1])
print 'Error statistics -> difference between ' + str(netx) + ' and ' + str(nety)
print 'Percent Difference: ' + str(round(pdiff,1)) + '%'
print 'Absolute Difference: ' + str(round(absdiff,2)) + ' inches'

fstatus.close()
#close('all') #closes all figure windows    
print 'Complete!'