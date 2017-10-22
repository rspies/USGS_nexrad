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
4.exceedence: calculate the exceedence probability of a input record from a
    txt file -> return a threshold value
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser
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
                                    x_lib[key].append(float(pgage)*gadj)
                                else:
                                    x_lib[key]=[float(pgage)*gadj]
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
    all_values_gage = {}
    all_values_nex = {}
    for line in txt_file:
        if line[:2] == '20': #ignores header
            pdata = line.split('\t')
            pgage = pdata[1].rstrip()
            pnex = pdata[2].rstrip()
            year = str(line[:4])
            date = pdata[0]
            if str(pgage).rstrip() != 'na' and date in temp_days[temp_criteria]:
                if float(pgage) >= 0:
                    if year in all_values_gage:
                        all_values_gage[year].append(float(pgage))
                    else:
                        all_values_gage[year] = [float(pgage)]
            
            if str(pnex).rstrip() != 'na' and date in temp_days[temp_criteria]:
                if float(pnex) >= 0:
                    if year in all_values_nex:
                        all_values_nex[year].append(float(pnex))
                    else:
                        all_values_nex[year] = [float(pnex)]
    ###### GAGE: calc exceedence values annually and append to year library ######
    for each_yr in all_values_gage:
        all_sort_gage = sorted(all_values_gage[each_yr], reverse=True)
        rank_gage = int(exceed_prob * (len(all_sort_gage) + 1))
        threshold = all_sort_gage[rank_gage - 1]
        if each_yr in yr_lib_gage:
            yr_lib_gage[each_yr].append(threshold)
        else:
            yr_lib_gage[each_yr] = [threshold]
    ###### GAGE: calc exceedence values annually and append to year library ######
    for each_yr in all_values_nex:
        all_sort_nex = sorted(all_values_nex[each_yr], reverse=True)
        rank_nex = int(exceed_prob * (len(all_sort_nex) + 1))
        threshold = all_sort_nex[rank_nex - 1]
        if each_yr in yr_lib_nex:
            yr_lib_nex[each_yr].append(threshold)
        else:
            yr_lib_nex[each_yr] = [threshold]

    return (yr_lib_gage,yr_lib_nex)
###############################################################################