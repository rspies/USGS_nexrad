#Created on Wed Apr 09 09:17:52 2014
#@author: rspies
# Python 2.7

"""
This script contains several functions for plotting different options:
1.colormap: adds a scatter plot of the data with a seperate z value used to
    produce a colormap
2.axis_limits: calculates the appropriate x/y axes max limit to maintain 1:1 comparison
3.annotate_dates: adds date labels to points at a specified interval
4.curve_fit: creats a polynomial trend line to the input data -> creates new x/y
    list values
5.annotate_number: labels points in a scatter plot with a predefined number label
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from dateutil import parser
import datetime


###############################################################################
def colormap(in_fig,axes,x,y,color_values,text):
    cmap = cm.jet_r # this sets the color scheme to jet (inversed)
    p =axes.scatter(x, y,c=color_values, cmap=cmap, marker='o', s=30, linewidth='0')
    if np.max(color_values)-np.min(color_values) < 10: # this fixes the issue with having decimal values in tick labels (want whole # gages)
        interval = 1
        tick_list = range(np.min(color_values),np.max(color_values)+1,interval)
        cbar = in_fig.colorbar(p, cmap=cmap, shrink=0.6, ticks=[tick_list])
    else:
        cbar = in_fig.colorbar(p, cmap=cmap, shrink=0.6)
    cbar.ax.set_ylabel(text, rotation=270,labelpad=15)
###############################################################################    
def axis_limits(x,y,axes):
    if max(x) > 100 or max(y) > 100:
        base = 25
    elif max(x) > 50 or max(y) > 50:
        base = 20
    elif max(x) > 25 or max(y) > 25:
        base = 10
    else:
        base = 5
    
    if max(x) > max(y):
        maximum = int(base * round((max(x)+(base))/base))
    else:
        maximum = int(base * round((max(y)+(base))/base))
    axes.set_ylim(0,maximum)
    axes.set_xlim(0,maximum)
    return(maximum)
###############################################################################
def annotate_dates(criteria,ystart,finish,date_plot,x,y,axes):
    date_list = []
    if criteria == 'Freeze':
        mn_tick = 12
        dy_tick = 31
    if criteria == 'Thaw':
        mn_tick = 9
        dy_tick = 30
    ticker = datetime.datetime(ystart, mn_tick, dy_tick, 0, 0)
    yr_cnt = 0
    while ticker <= finish:
        if str(ticker) in date_plot:
            date_list.append(str(ticker))
        elif str(ticker + datetime.timedelta(days =1)) in date_plot:
            date_list.append(str(ticker + datetime.timedelta(days =1)))
        elif str(ticker - datetime.timedelta(days =1)) in date_plot:
            date_list.append(str(ticker - datetime.timedelta(days =1)))
        yr_cnt += 1
        ticker = datetime.datetime(ystart + yr_cnt, mn_tick, dy_tick, 0, 0)
    date_list.append(date_plot[0]) # add first date
    date_list.append(date_plot[len(date_plot)-1]) # add last date
    date_list = sorted(date_list) # sort the cronologically
    tick_cnt = 1
    if len(date_list) >= 10: # reduce the number of labels to prevent overcrowding
        for each in date_list:
            if each != min(date_list) or each != max(date_list):
                if tick_cnt%2== 0: # remove even ticks
                    date_list.remove(each)
            tick_cnt += 1 
    
    for tick_yr in date_list: # always label first and last data point
        if tick_yr == min(date_list) or tick_yr == date_list[1]:
            axes.annotate(tick_yr[:-9], xy=(x[date_plot.index(tick_yr)], 
                            y[date_plot.index(tick_yr)]),  xycoords='data',
                            xytext=(50, 10), textcoords='offset points',
                            arrowprops=dict(arrowstyle="->"))
        elif tick_yr == max(date_list):
            axes.annotate(tick_yr[:-9], xy=(x[date_plot.index(tick_yr)], 
                            y[date_plot.index(tick_yr)]),  xycoords='data',
                            xytext=(-30, -70), textcoords='offset points',
                            arrowprops=dict(arrowstyle="->"))
        else:
            axes.annotate(tick_yr[:-9], xy=(x[date_plot.index(tick_yr)], 
                            y[date_plot.index(tick_yr)]),  xycoords='data',
                            xytext=(-50, 30), textcoords='offset points',
                            arrowprops=dict(arrowstyle="->"))
###############################################################################
def curve_fit(x,y):
    # calculate polynomial
    z = np.polyfit(x, y, 5)
    f = np.poly1d(z)
    # solve for y=0.5 (50%)
    p = np.polynomial.Polynomial.fit(x,y,5)
    solve = (p -50).roots()
    
    # calculate new x's and y's
    x_new = np.linspace(x[0], x[-1], 50)
    y_new = f(x_new)
    return (x_new, y_new,solve)
###############################################################################  
def annotates_number(in_lib,xin,yin,axes,numbers):
    x = []
    y = []
    acnt = 0
    for stations in in_lib:
        trigger = 'no'
        bcnt = 0
        if len(x) != 0:   
            for each in x:
                # the following tries to determine points that are too close 
                # and move their label position
                if xin[acnt] < each + 5 and xin[acnt] > each - 5:
                    if yin[acnt] < y[bcnt] + 5 and yin[acnt] > y[bcnt] - 5:
                        axes.annotate(numbers[stations[:-4]], xy=(xin[acnt], yin[acnt]),
                                     xycoords='data',xytext=(5, -10), textcoords='offset points')
                        trigger = 'yes'
                        break
                else:
                    trigger = 'no'
                bcnt += 1
        # keep a list of the annotated points to determine if the next point
        # is too close to any previous point
        if trigger == 'no':            
            axes.annotate(numbers[stations[:-4]], xy=(xin[acnt], yin[acnt]),
                         xycoords='data',xytext=(5, 5), textcoords='offset points')
        x.append(xin[acnt]); y.append(yin[acnt])
        acnt += 1           
        