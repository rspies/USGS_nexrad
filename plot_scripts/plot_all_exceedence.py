#Created on Wed Apr 16 14:30:52 2014
#@author: rspies
# Python 2.7
# This script reads the newly created Arogonne freeze/thaw file along with all of the
# paired ground-gage/nexrad data files
# Outputs a exceedence precipitation plot 

import os
import datetime
from dateutil import parser
import matplotlib.pyplot as plt
import module_parse_txt
import scipy.stats as scistat
plt.ioff()
os.chdir("..")
maindir = os.getcwd() + os.sep

fig = plt.figure()
ax1 = fig.add_subplot(111)

############# USER INPUT BLOCK ###############################################
gage_nets = ['usgs'] # choices: 'cocorahs','usgs' 
# NEXRAD data will be pulled from paired files in gage_nets
criteria = 'Thaw' # choicea are 'Freeze' or 'Thaw' #see find_freeze_days.py for more info
exceed_prob_list = [0.001,0.01, 0.025, 0.05, 0.10, 0.25] # decimal exceendence probablity option (enter 0 to ignore)

padj = 1.14 # Precip Adjustment Factor (snowcf applied below)
if padj > 1.0:
    text = '(PADJ=' + str(padj) + ')'
else:
    text = ''
#################################################################################
## calculate z-score for x axis labels
probs = []; zscore = []
for each in exceed_prob_list:
    probs.append(1-each)
zscores = scistat.norm.ppf(probs).tolist()
zscore = [round(elem, 2) for elem in zscores]
################# create a list of days to use in the analysis ########################
ystart = yone = 2007 # begin data grouping
if gage_nets == ['usgs']:
    ystart = yone = 2002
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 2, 1, 0, 0)
finish = datetime.datetime(yend, 9, 30, 23, 0)
years = []
while ystart <= yend:
    years.append(ystart)
    ystart += 1
    
########create variable data libraries #######
cocorahs_list = []; usgs_list = []
nex_coco = []; nex_usgs = []
cnt = 0
######### create a list of the exceedence values in percent (convert from decimal)
percent_exceed = [] 
for each in exceed_prob_list:
    percent_exceed.append(round(each*100,1))

for gage_net in gage_nets:
    cnt += 1
    ####### apply SNOWCF to USGS gages ####
    if criteria == 'Freeze' and gage_net == 'usgs' and padj > 1.0:
        scf = 1.0
    else:
        scf = 1.0
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
    
    print 'Searching through paired gage/nexrad data...'
    all_gage = [] # list of all gage data for all years
    if cnt == 1: # only create the all nexrad list for the first input gage network
        all_nex = [] # want to cumulate nexrad data for all gage networks
    pfiles = os.listdir(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\')    
    for each_pair in pfiles:
        miss_cnt = 0
        if each_pair[:1] != 's' and each_pair[:-4] in gages_met: #ignores status.txt file
            txt_file = open(maindir + 'data\\' + gage_net[:4] + '_nexrad_paired\\' + each_pair ,'r')
            print each_pair       
            for line in txt_file:
                if line[:2] == '20': #ignores header
                    pdata = line.split('\t')
                    pgage = pdata[1].rstrip()
                    pnex = pdata[2].rstrip()
                    year = str(line[:4])
                    date = pdata[0]
                    #if pgage != 'na' and pnex != 'na': # only use daily data when both gage and nexrad data available
                    if str(pgage).rstrip() != 'na' and date in temp_lib[criteria]:
                        if float(pgage) >= 0: # create a list of precip values >= 0.0in
                            all_gage.append(float(pgage))
                    
                    if str(pnex).rstrip() != 'na' and date in temp_lib[criteria]:
                        if float(pnex) >= 0:  # create a list of precip values >= 0.0in
                            all_nex.append(float(pnex))                      
            txt_file.close()

    print 'Processing exceedance probability: '
    all_gage_exceed,all_nex_exceed = module_parse_txt.exceedence_all_years(all_gage,all_nex,exceed_prob_list,gage_net,gage_nets,cnt,padj)
    print all_gage_exceed
    print all_nex_exceed
############################## Create Figure ####################################       
    if gage_net == 'usgs':
        if criteria == 'Freeze':
            gtype = 'Heated '
        else:
            gtype = ''
        if padj != 1.0:
            lab = 'Adjusted ' + gtype + 'USGS Gages '
        else:
            lab = gtype + 'USGS Gages '
        ax1.plot(zscore, all_gage_exceed, ls='-', color='blue', marker = 'o', lw=1.75, label = lab + text)
#        if padj != 1.0:
#            lab = 'Adjusted NEXRAD-MPE (USGS pair) '
#        else:
#            lab = 'NEXRAD-MPE (USGS pair) '
#        ax1.plot(zscore, all_nex_exceed, ls='--', color='cyan', marker = 's', lw=1.75, label = lab + text)        
        
    if gage_net == 'cocorahs':
        ax1.plot(zscore, all_gage_exceed, ls='-', color='gold', marker = 'o', lw=1.75, label = 'CoCoRaHS Gages')
#        if padj != 1.0:
#            lab = 'Adjusted NEXRAD-MPE (CoCoRaHS pair) '
#        else:
#            lab = 'NEXRAD-MPE (CoCoRaHS pair) '
#        ax1.plot(zscore, all_nex_exceed, ls='--', color='orange', marker = 's', lw=1.75, label = lab + text) 

    if cnt == len(gage_nets):
        if padj != 1.0:
            lab = 'Adjusted NEXRAD-MPE '
        else:
            lab = 'NEXRAD-MPE '
        ax1.plot(zscore, all_nex_exceed, ls='--', color='red', marker = 's', lw=1.75, label = lab + text)

##################### Add labels and Gridlines ##################################
ax1.set_ylabel('Precipitation depth (inches)\n',labelpad=-10)
#ax1.set_xlabel('Daily Exceedence Probability (Percent)')
ax1.set_xlabel('Exceedance probability')
ax1.set_xticks(zscore) # only show the exceedence prob tick marks
ax1.set_xticklabels(exceed_prob_list,rotation=90)
ax1.set_yscale('log') # logarithmic y-axis scale
#ax1.set_ylim([0.01,5])
from matplotlib.ticker import ScalarFormatter
ax1.yaxis.set_major_formatter(ScalarFormatter())

if criteria == 'Thaw':
    text = 'Nonfreezing days'
if criteria == 'Freeze':
    text = 'Freezing days'

#ax1.set_title('Daily Precipitation Quantiles\n' + text + ': ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + ' - ' + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year))
ax1.set_title(text + ', ' + str(start.month)+'/'+str(start.day)+'/'+str(start.year) + u"\u2013" + str(finish.month)+'/'+str(finish.day)+'/'+str(finish.year))
ax1.grid(True)
ax1.legend(loc='best',numpoints = 1, fontsize=11.5)

if len(gage_nets) > 1:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\precip_quantiles\\' + 'All_percent_exceedance_padj.png', dpi=150, bbox_inches='tight')
else:
    plt.savefig(maindir + '\\figures\\final\\' + criteria.lower() + '_days\\precip_quantiles\\' + gage_net + '_only_percent_exceedance_padj.png', dpi=150, bbox_inches='tight')
#close('all') #closes all figure windows    
print 'Complete!'