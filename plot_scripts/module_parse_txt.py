#Created on Wed Apr 16 14:30:52 2014
#@author: rspies
# Python 2.7

"""
This script contains several functions for parsing text files:
1.find_gages: searches through the proper info txt file for the input gage
    network and creates a list of stations used in analysis
2.get_gage_data: searches through the appropriate gage network individual paired
    site files and creates a library of available data for each day
3.pcnt_rain_snow: calculates a list of the percent of total observations 
    that are rain or snow
4.exceedence: calculate the quantile value from a list of exceedence probabilities 
    of an input list and calculate Maritz-Jarrett standard error -> return a 
    threshold value
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser
from scipy import stats
import datetime

###############################################################################
def find_gages(maindir,criteria,netx,nety):
    gages_met1 = []; gages_met2 = []
    if netx == 'usgs':
        ftype = open(maindir + 'data\\INPUT_gages_cells.txt','r')
        for every in ftype:
            if every[:4] != 'Loca': #ignore header line
                idinfo = every.split('\t')
                station_id = idinfo[1].rstrip()
                type_gage = idinfo[3].rstrip()
                if criteria == 'Thaw':
                    gages_met1.append(station_id)
                elif criteria == 'Freeze':
                    if type_gage == 'Y':
                        gages_met1.append(station_id)
        print str(netx.upper()) + ': ' + str(len(gages_met1)) + ' available gages'
    if netx == 'cocorahs' or nety == 'cocorahs':
        ftype = open(maindir + 'data\\INPUT_coco_cells_distance.txt','r')
        for every in ftype:
            idinfo = every.split('\t')
            if every[:4] == 'COCO': #ignores header
                #name = idinfo.index('Name')
                num = idinfo.index('Site_ID')
                #rad_cell = idinfo.index('CELL_NO')
            else:
                station_id = idinfo[num].rstrip()
                gages_met2.append(station_id)
        print 'COCORAHS: ' + str(len(gages_met2)) + ' available gages'
        if nety == 'nexrad':
            gages_met1 = gages_met2
            gages_met2 = []
    return (gages_met1, gages_met2)
    
###############################################################################
def get_gage_data(maindir,netx,nety,start,finish,gages_met1,gages_met2,gadj,nexadj,scf,x_lib,y_lib):    
    pfiles = os.listdir(maindir + 'data\\' + netx[:4] + '_nexrad_paired\\')    
    for each_pair in pfiles:
        if each_pair[:1] != 's': #ignores status.txt file
            if each_pair[:-4] in gages_met1:
                print each_pair
                popen = open(maindir + 'data\\' + netx[:4] + '_nexrad_paired\\' + each_pair ,'r')
                for line in popen:
                    if line[:2] == '20': #ignores header
                        pdata = line.split('\t')
                        date_check = parser.parse(pdata[0])
                        if date_check >= start and date_check <= finish:        
                            pgage = pdata[1].rstrip()
                            pnex = pdata[2].rstrip()
                            if pgage != 'na' and pnex != 'na':
                                key = str(date_check)
                                if key in x_lib:
                                    x_lib[key].append((float(pgage)*gadj)*scf)
                                else:
                                    x_lib[key]=[(float(pgage)*gadj)*scf]
                                if nety == 'nexrad': # only populate y array here if using nexrad data
                                    if key in y_lib:
                                        y_lib[key].append(float(pnex)*nexadj)
                                    else:
                                        y_lib[key]=[float(pnex)*nexadj]                               
                popen.close()
    if nety != 'nexrad':
        pfiles = os.listdir(maindir + 'data\\' + nety[:4] + '_nexrad_paired\\')    
        for each_pair in pfiles:
            if each_pair[:1] != 's': #ignores status.txt file
                if each_pair[:-4] in gages_met2:
                    print each_pair
                    popen = open(maindir + 'data\\' + nety[:4] + '_nexrad_paired\\' + each_pair ,'r')
                    for line in popen:
                        if line[:2] == '20': #ignores header
                            pdata = line.split('\t')
                            date_check = parser.parse(pdata[0])
                            if date_check >= start and date_check <= finish:        
                                pgage = pdata[1].rstrip()
                                pnex = pdata[2].rstrip()
                                if pgage != 'na' and pnex != 'na':
                                    key = str(date_check)
                                    if key in y_lib:
                                        y_lib[key].append(float(pgage))
                                    else:
                                        y_lib[key]=[float(pgage)]
                    popen.close()
    return(x_lib, y_lib)  
###############################################################################
def pcnt_rain_snow(rain,snow,categories,rpcnt,spcnt,x):
    num_cat = 1
    while num_cat <= len(categories): 
        kitty = 'cat' + str(num_cat)
        mean_cat = round(np.mean(categories[kitty]),2)
        if kitty in snow:
            tot_snow = len(snow[kitty])
        else:
            tot_snow = 0
        if kitty in rain:
            tot_rain = len(rain[kitty])
        else:
            tot_rain = 0
        tot_all = tot_snow + tot_rain
        if tot_all > 0: # ignores the categories without data (ncdc data rounding issue)
            spcnt.append(round((float(tot_snow)/tot_all)*100,1))
            rpcnt.append(round((float(tot_rain)/tot_all)*100,1))
            x.append(mean_cat)
        num_cat += 1
###############################################################################
def exceedence(txt_file,exceed_prob,temp_days,temp_criteria,yr_lib_gage,yr_lib_nex):  
    all_values_gage = {}; all_values_nex = {}
    for line in txt_file:
        if line[:2] == '20': #ignores header
            pdata = line.split('\t')
            pgage = pdata[1].rstrip()
            pnex = pdata[2].rstrip()
            year = str(line[:4])
            date = pdata[0]
            if str(pgage).rstrip() != 'na' and date in temp_days[temp_criteria]:
                if float(pgage) >= 0:  # create a list of precip values >= 0.0in
                    if year in all_values_gage:
                        all_values_gage[year].append(float(pgage))
                    else:
                        all_values_gage[year] = [float(pgage)]
            
            if str(pnex).rstrip() != 'na' and date in temp_days[temp_criteria]:
                if float(pnex) >= 0:  # create a list of precip values >= 0.0in
                    if year in all_values_nex:
                        all_values_nex[year].append(float(pnex))
                    else:
                        all_values_nex[year] = [float(pnex)]
    ###### GAGE: calc exceedence values annually and append to year library ######
    for each_yr in all_values_gage:
        all_sort_gage = sorted(all_values_gage[each_yr], reverse=True)
        rank_gage = int(exceed_prob * (len(all_sort_gage) + 1))
        threshold = all_sort_gage[rank_gage - 1]
        # the following if statement accounts for the issue when there are less than
        # 100 daily values -> causes errors with the rank value being set to -1
        # Minimum rank set to 1 (actually 0 index) 
        #if exceed_prob < 2.5 and rank_gage <= 0 and len(all_sort_gage) < 100:
        #    threshold = all_sort_gage[rank_gage]
        if each_yr in yr_lib_gage:
            yr_lib_gage[each_yr].append(threshold)
        else:
            yr_lib_gage[each_yr] = [threshold]
    ###### GAGE: calc exceedence values annually and append to year library ######
    for each_yr in all_values_nex:
        all_sort_nex = sorted(all_values_nex[each_yr], reverse=True)
        rank_nex = int(exceed_prob * (len(all_sort_nex) + 1))
        threshold = all_sort_nex[rank_nex - 1]
        # the following if statement accounts for the issue when there are less than
        # 100 daily values -> causes errors with the rank value being set to -1
        # Minimum rank set to 1 (actually 0 index) 
        #if exceed_prob < 2.5 and rank_nex <= 0 and len(all_sort_nex) < 100:
        #    threshold = all_sort_nex[rank_nex]
        if each_yr in yr_lib_nex:
            yr_lib_nex[each_yr].append(threshold)
        else:
            yr_lib_nex[each_yr] = [threshold]

    return (yr_lib_gage,yr_lib_nex)
    
###############################################################################
def exceedence_years(txt_file,exceed_prob,temp_days,temp_criteria,all_values_all_gages,all_values_all_nex,gage_cnt,num_gages):  
    yr_lib_all_gages={}; yr_lib_all_nex={}
    for line in txt_file:
        if line[:2] == '20': #ignores header
            pdata = line.split('\t')
            pgage = pdata[1].rstrip()
            pnex = pdata[2].rstrip()
            year = str(line[:4])
            date = pdata[0]
            if str(pgage).rstrip() != 'na' and date in temp_days[temp_criteria]:
                if float(pgage) >= 0:  # create a list of precip values >= 0.0in
                    #keep a running dictionary with data for all gages
                    if year in all_values_all_gages:
                        all_values_all_gages[year].append(float(pgage))
                    else:
                        all_values_all_gages[year] = [float(pgage)]
            
            if str(pnex).rstrip() != 'na' and date in temp_days[temp_criteria]:
                if float(pnex) >= 0:  # create a list of precip values >= 0.0in
                    #keep a running dictionary with data for all gages/cells
                    if year in all_values_all_nex:
                        all_values_all_nex[year].append(float(pnex))
                    else:
                        all_values_all_nex[year] = [float(pnex)]

    # perform exceendance calculations using data for all gages as opposed to by gage from above
    print gage_cnt
    
    ###### GAGE: calc exceedence values annually and append to year library ######
    for each_yr in all_values_all_gages:
        all_sort_gage = sorted(all_values_all_gages[each_yr], reverse=True)
        rank_gage = int(exceed_prob * (len(all_sort_gage) + 1))
        threshold = all_sort_gage[rank_gage - 1]
        yr_lib_all_gages[each_yr] = [threshold]
    ###### GAGE: calc exceedence values annually and append to year library ######
    for each_yr in all_values_all_nex:
        all_sort_nex = sorted(all_values_all_nex[each_yr], reverse=True)
        rank_nex = int(exceed_prob * (len(all_sort_nex) + 1))
        threshold = all_sort_nex[rank_nex - 1]
        yr_lib_all_nex[each_yr] = [threshold]

    return (yr_lib_all_gages,yr_lib_all_nex,all_values_all_gages,all_values_all_nex)
###############################################################################

def exceedence_all_years(all_gage,all_nex,exceed_prob_list,gage_net,gage_nets,cnt,padj):  
    all_gage_exceed = [] # create a library of annual data for gage data
    all_nex_exceed = [] # create a library of annual data for nexrad data
    for exceed_prob in exceed_prob_list:
        ###### GAGE: calc exceedence values annually and append to year library ######
        all_sort_gage = sorted(all_gage, reverse=True)
        rank_gage = int(exceed_prob * (len(all_sort_gage) + 1))
        threshold = all_sort_gage[rank_gage - 1]
        if gage_net == 'usgs':
            all_gage_exceed.append(float(threshold)*padj)
        else:
            all_gage_exceed.append(threshold)
        
        ###### NEXRAD: calc exceedence values annually and append to list ######
        if cnt == len(gage_nets): # only do NEXRAD analysis when we have all NEXRAD data in list
            all_sort_nex = sorted(all_nex, reverse=True)
            rank_nex = int(exceed_prob * (len(all_sort_nex) + 1))
            threshold = all_sort_nex[rank_nex - 1]
            all_nex_exceed.append(float(threshold)*padj)
    exceed = []
    for each in exceed_prob_list:
        exceed.append(1-each)
    print exceed
    #exceed = np.array(exceed_prob_list)
    mj_gage_error = stats.mstats_extras.mjci(all_sort_gage, exceed)
    print 'Gage Net: ' + str(gage_net)
    print 'Maritz-Jarrett Error: ' + str(mj_gage_error)
    if cnt == len(gage_nets):
        mj_nex_error = stats.mstats_extras.mjci(all_sort_nex, exceed)
        print 'NEXRDAD: MPE:'
        print 'Maritz-Jarrett Error: ' + str(mj_nex_error)

    return (all_gage_exceed,all_nex_exceed)
###############################################################################    
    