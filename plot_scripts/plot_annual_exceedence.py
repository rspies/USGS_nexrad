#Created on Wed Apr 16 14:30:52 2014
#@author: rspies
# Python 2.7
# This script reads the newly created Arogonne freeze/thaw file along with all of the
# paired ground-gage/nexrad data files
# Outputs a exceedence precipitation plot 

import os
import datetime
from dateutil import parser
import numpy
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
import module_parse_txt
plt.ioff()
os.chdir("..")
maindir = os.getcwd() + os.sep

############# USER INPUT BLOCK ###############################################
gage_nets = ['cocorahs','usgs'] # choices: 'usgs' or 'cocorahs'
criteria = 'Freeze' # choicea are 'Freeze' or 'Thaw' #see find_freeze_days.py for more info
exceed_prob_list = [0.025, 0.05, 0.10, 0.25] # decimal exceendence probablity option (enter 0 to ignore)
padj = 1.14
################# create a list of days to use in the analysis ########################

for exceed_prob in exceed_prob_list:
    print 'Processing exceedance probability: ' + str("%.1f" % float(exceed_prob*100))
    print 'Searching through paired gage/nexrad data...'
    count = 0
    for gage_net in gage_nets:
        count += 1
        if gage_net == 'usgs':
            ystart = 2002 # begin data grouping
        if gage_net == 'cocorahs':
            ystart = 2007 # begin data grouping
        yend = 2012 # end data grouping
        start = datetime.datetime(ystart, 2, 1, 0, 0)
        finish = datetime.datetime(yend, 9, 30, 23, 0)
        years = []
        while ystart <= yend:
            years.append(ystart)
            ystart += 1
            
        if gage_net == 'cocorahs':
            gage_name = 'CoCoRaHS'
        else:
            gage_name = gage_net.upper()
        
        #################### Begin parsing txt files ########################################
        print str(start) + ' - ' + str(finish)
        ################## Parse Argonne temperature file ################################    
        # Loop through the Agronne temperature freeze criteria file previously generated
        # Create a dictionary of dates for both the freeze and thaw criteria
        print 'Examing:' + criteria + ' days and ' + gage_net.upper() + ' gages...'
        print 'Processing data for ' + 'Argonne hourly freeze/thaw data...'
        if gage_net == 'usgs':
            fopen = open(maindir + 'data\\temperature\\argonne_freeze.txt','r')
        elif gage_net == 'cocorahs':
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
                        temp_lib[temp].append(str(date_check)[:10])
                    elif temp == 'Freeze':
                        temp_lib[temp].append(str(date_check)[:10])
                    else:
                        print 'Error in Agronne freeze/thaw file: ' + date_check
                    if temp == criteria:
                        t_days += 1
        fopen.close()
        ############# Search through heated, unheated, or all gages in info txt file  ####################
        #### Also find station # for annotating points on plot
        net_dummy = '' # need this to use my function
        if gage_net == 'usgs':
            gages_met,dummy = module_parse_txt.find_gages(maindir,criteria,gage_net,net_dummy)    
        if gage_net == 'cocorahs':
            dummy, gages_met = module_parse_txt.find_gages(maindir,criteria,gage_net,net_dummy)
                    
        ###################### Search through paired gage/nexrad files  ####################    
        # Loop through all paired Gage/NEXRAD files and create a dictionay of data
        # for each data found in the paired files
        yr_lib_gage = {} # create a library of annual data for gage data
        if count == 1: # only initialize (create empty) dictionary for the first gage_net -> allows nexrad data to include pairs for all gage_nets
            yr_lib_nex = {}; all_values_all_nex={} # create a library of annual data for nexrad data
        pfiles = os.listdir(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\')    
        all_values_all_gages={}; num_gages = len(pfiles)
        gage_cnt = 0
        for each_pair in pfiles:
            gage_cnt += 1
            if each_pair[:1] != 's' and each_pair[:-4] in gages_met: #ignores status.txt file
                popen = open(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\' + each_pair ,'r')
                #print each_pair
                import module_parse_txt
                time_period = 'annual' # this tells the module to compute theshold values annually
                yr_lib_gage,yr_lib_nex = module_parse_txt.exceedence(popen,exceed_prob,temp_lib,criteria,yr_lib_gage,yr_lib_nex)
                popen.close()
                popen = open(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\' + each_pair ,'r')
                yr_lib_all_gages,yr_lib_all_nex,all_values_all_gages,all_values_all_nex = module_parse_txt.exceedence_years(popen,exceed_prob,temp_lib,criteria,all_values_all_gages,all_values_all_nex,gage_cnt,num_gages)
                popen.close()
          
        ############ Check to use only years containing adequate data #######
        years_plot = []
        print years
        for each_year in years:
            print 'Processing: ' + str(each_year)
            if str(each_year) in yr_lib_gage:
                # need at least 10 stations reporting for a year
                # unless using heated usgs gages (5 required)
                if len(yr_lib_gage[str(each_year)]) >= 10 or gage_net == 'usgs' and criteria == 'Freeze' and len(yr_lib_gage[str(each_year)]) >= 3: 
                    years_plot.append(int(each_year))
                    print 'included ' + str(each_year)
                #else:
                #    yr_lib_gage[str(each_year)]
                #    yr_lib_nex[str(each_year)]
        print years_plot
        
        ############ create x/y plotting variables #######################         
        in_gage = []; in_nex = []
        for all_site_gage in years_plot:
            if gage_net == 'usgs' and padj > 1.0:
                in_gage.append(round(numpy.mean(yr_lib_all_gages[str(all_site_gage)])*padj,3))
            else:
                in_gage.append(round(numpy.mean(yr_lib_all_gages[str(all_site_gage)]),3))
        for all_site_nex in years_plot:
            if padj > 1.0:
                print 'PADJ = ' + str(padj)
                in_nex.append(round(numpy.mean(yr_lib_all_nex[str(all_site_nex)])*padj,3))
            else:
                in_nex.append(round(numpy.mean(yr_lib_all_nex[str(all_site_nex)]),3))
        print in_gage
        print in_nex
    
        ############################## Create Figure ####################################       
        if count == 1:
            fig = plt.figure()
            ax1 = fig.add_subplot(211)
        if gage_net == 'usgs' and padj != 1.0:
            ax1.plot(years_plot, in_gage, ls='-', color='blue', lw=1.75,  marker = 'o', ms=4, label = str('Adjusted ' + gage_name + ' gages (PADJ=' + str(padj) +')'))
        elif gage_net == 'cocorahs':
            ax1.plot(years_plot, in_gage, ls='-', color='gold', lw=1.75, marker = 'o', ms=4, label = str(gage_name + ' gages'))
        else:
            ax1.plot(years_plot, in_gage, ls='-', color='blue', lw=1.75, marker = 'o', ms=4, label = str(gage_name + ' gages'))
        if count == len(gage_nets):
            if padj != 1.0:
                ax1.plot(years_plot, in_nex, ls='--', color='red', lw=1.75, marker = 's', ms=4, label = 'Adjusted NEXRAD-MPE (PADJ=' + str(padj) +')')
            else:
                ax1.plot(years_plot, in_nex, ls='--', color='red', lw=1.75, marker = 's', ms=4, label = 'NEXRAD-MPE')
            ##################### Add labels and Gridlines ##################################
            ax1.set_ylabel('Precipitation depth (inches)')
            ax1.set_xlabel('Calendar year')
            ax1.set_ylim(0)
            ax1.xaxis.set_major_locator(MaxNLocator(nbins = len(years_plot)-1))
            ax1.set_xticklabels(years_plot,fontsize=11) # this is a work around for xtick label issue when plotting major x ticks
            '''
            if gage_net == 'cocorahs':
                ax1.set_xticklabels(years_plot)  # this is a work around for xtick label issue when plotting cocorahs data      
                ax1.tick_params(axis='both', which='major', labelsize=10)
            if gage_net == 'usgs':
                ax1.set_xticklabels(years_plot[::2])  # this is a work around for xtick label issue when plotting cocorahs data      
                ax1.tick_params(axis='both', which='major', labelsize=10)
            '''
            #ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1f'))
            if criteria == 'Thaw':
                text = 'Non-freezing Days'
            if criteria == 'Freeze':
                text = 'Freezing Days'
            if exceed_prob >= 0.05:
                exceed_text = str(int(exceed_prob*100))
            else:
                exceed_text = str("%.1f" % float(exceed_prob*100))
            ax1.set_title(exceed_text + '% Exceedance probability quantiles')
            ax1.grid(True)
            ax1.legend(loc='best',prop={'size':11},framealpha=0.6)
            if len(gage_nets) > 1:
                gage_net_title = 'all_gages'
            else:
                gage_net_title = gage_net
            if padj > 1.0:
                plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\precip_quantiles\\' + gage_net_title + '_' + str(int(exceed_prob*100)) + '_percent_exceedance_padj.png', dpi=150, bbox_inches='tight')
            else:
                plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\precip_quantiles\\' + gage_net_title + '_' + str(int(exceed_prob*100)) + '_percent_exceedance.png', dpi=150, bbox_inches='tight')
#close('all') #closes all figure windows    
print 'Complete!'