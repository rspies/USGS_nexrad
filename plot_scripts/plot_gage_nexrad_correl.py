#Created on Fri March 24 08:37:17 2014
#@author: rspies
# Python 2.7
# This script reads the newly created Arogonne freeze/thaw file along with all of the
# paired ground-gage/nexrad data files
# Outputs a single pointwise total plot comparing totoal precip for each gage agains corresponding NEXRAD cell value

import os
import datetime
from dateutil import parser
import matplotlib
import matplotlib.pyplot as plt
import calc_errors
plt.ioff()
os.chdir("..")
maindir = os.getcwd() + os.sep

criteria = 'Freeze' # choicea are 'Freeze' or 'Thaw' #see find_freeze_days.py for more info
gage_types = ['All','Heated','Non-Heated']
point_labels = 'no' # choices: 'yes', 'no' #plot point number labels
padj = 1.14 # 1.14 apply the precip adj factor to both nexrad and usgs gage data
if criteria == 'Freeze': # apply snow catchment factor to usgs gages
    scf = 1.0
else:
    scf = 1.0

################# create a list of days to use in the analysis ########################
ystart = 2007 # begin data grouping
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 2, 1, 0, 0)
finish = datetime.datetime(yend, 9, 30, 23, 0)

for gage_type in gage_types:
    fstatus = open(maindir + '\\figures\\final\\status_files\\usgs_' + gage_type + '_stations_stats_' + criteria + '_' + str(ystart) + '_' + str(yend) + '.txt', 'w')
    fstatus.write(str(start) + ' - ' + str(finish) + '\n')
    fstatus.write('Station' + '\t' + 'Missing days in analysis\n')
    print str(start) + ' - ' + str(finish)
    ################## Parse Argonne temperature file ################################    
    # Loop through the Agronne temperature freeze criteria file previously generated
    # Create a dictionary of dates for both the freeze and thaw criteria
    print 'Examing:' + criteria + ' days and ' + gage_type + ' gages...'
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
    ############# Search through heated, unheated, or all gages in info txt file  ####################
    #### Also find station # for annotating points on plot
    ftype = open(maindir + 'data\\INPUT_gages_cells.txt','r')
    gages_met = []
    gages_nums = {}
    for every in ftype:
        if every[:4] != 'Loca':
            idinfo = every.split('\t')
            station_id = idinfo[1].rstrip()
            type_gage = idinfo[3].rstrip()
            gage_num = idinfo[4].rstrip()
            gages_nums[str(station_id)] = str(gage_num)
            if gage_type == 'All':
                gages_met.append(station_id)
            elif gage_type == 'Heated':
                if type_gage == 'Y':
                    gages_met.append(station_id)
            elif gage_type == 'Non-Heated':
                if type_gage == 'N' or type_gage == '':
                    gages_met.append(station_id)
            else:
                print 'Gage-type input error -> check input in script header'
            
    ###################### Search through paired gage/nexrad files  ####################    
    # Loop through all paired Gage/NEXRAD files and create a dictionay of data
    # for each data found in the paired files
    print 'Searching through paired gage/nexrad data...'
    gage_lib = {}
    nex_lib = {}
    pfiles = os.listdir(maindir + 'data\\usgs_nexrad_paired\\')    
    for each_pair in pfiles:
        miss_cnt = 0
        if each_pair[:1] != 's' and each_pair[:-4] in gages_met: #ignores status.txt file
            popen = open(maindir + 'data\\usgs_nexrad_paired\\' + each_pair ,'r')
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
                                gage_lib[key].append(float(pgage)*scf)
                            else:
                                gage_lib[key]=[float(pgage)*scf]
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
            total_nex = sum(nex_lib[station])
            in_gage.append(total_gage*padj) # apply the precip adjustment factor
            in_nex.append(total_nex*padj)   # apply the precip adjustment factor
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

    if (minimum - 20) < 0:
        min_axis = 0
    else:
        min_axis = minimum - 20
    ax1.set_ylim([min_axis,maximum + 20])
    ax1.set_xlim([min_axis,maximum + 20])
    
    ################### Calculate Error Statistics and add to plot ################
    pbias, mae, ns = calc_errors.print_errors(in_gage,in_nex)
    textstr = '\nMean Percent Difference:\n' + r'$\frac{1}{n}\sum_{i=1}^n\frac{(y_i-x_i)}{x_i}$ = ' + str('%.1f' % pbias) +'%\n\n' + 'Mean Absolute Difference:\n ' + r'$\frac{1}{n}\sum_{i=1}^n\vert y_i - x_i\vert$ = '+ str('%.2f' % mae) + ' in'  #Mean Absolute Difference
    # these are matplotlib.patch.Patch properties
    props = dict(boxstyle='round', facecolor = '0.8', alpha=0.5)
    
    # place a text box in upper left in axes coords
    ax1.text(0.03, 0.97, textstr, transform=ax1.transAxes, fontsize=12.5,
            verticalalignment='top', bbox=props)
    
    ###### OPTION: annotate site number labels without overlapping
    if point_labels == 'yes':
        import my_plot_module
        my_plot_module.annotates_number(gage_lib,in_gage,in_nex,ax1,gages_nums)
    
    ##################### Add labels and Gridlines ##################################
    if padj != 1.0 or scf != 1.0:
        text = 'Adjusted '
    else:
        text = ''
    ax1.set_ylabel('Total ' + text + 'NEXRAD-MPE Precipitation (inches)')
    ax1.set_xlabel('Total ' + text + 'USGS Gage Precipitation (inches)')
    if criteria == 'Thaw':
        text = 'Non-freezing Days'
    if criteria == 'Freeze':
        text = 'Freezing Days'
    ax1.set_title('Pointwise Total of Gages and Overlying NEXRAD cells\n' + gage_type + ' USGS Gages, ' + text + ': ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + ' - ' + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year))
    ax1.grid(True)
    ax1.legend(loc='lower right',numpoints = 1)
    
    if padj != 1.0:
        plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\usgs_gages\\' + gage_type + '_station_correlation_' + criteria + '_days_' + str(ystart) + '_padj' + '.png', dpi=150, bbox_inches='tight')
    else:
        plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\usgs_gages\\' + gage_type + '_station_correlation_' + criteria + '_days_' + str(ystart) + '.png', dpi=150, bbox_inches='tight')
#close('all') #closes all figure windows    
print 'Complete!'