# error statistics
import numpy as np
def print_errors(obsx,modely):
    print 'Length of sim: ' + str(len(modely))
    print 'Length of obs: ' + str(len(obsx))
    cnt = 0
    a = 0
    b = 0
    for each in modely:
        a = a + (modely[cnt] - obsx[cnt])
        b = sum(obsx)
        cnt += 1
    pbias = round((a/b) * 100,1)
    print 'P Bias: ' + str(pbias)
    ###### Nash Sutcliffe #####
    cnt = 0
    a = 0
    c = 0
    for each in modely:
        a = a + ((modely[cnt] - obsx[cnt])**2)
        b = sum(obsx)/len(obsx)
        c = c + ((obsx[cnt] - b)**2)
        cnt += 1
    ns = round(1 - (a/c), 2)
    print 'NSE: ' + str(ns)
    ###### Mean Absolute Error #####
    cnt = 0
    a = 0
    for each in modely:
        a = a + (abs(modely[cnt] - obsx[cnt]))
        cnt += 1
    mae = round(a/len(modely),2)
    print 'MAE: ' + str(mae)
    ###### Normalized (mean obs) Root Mean Squared Error #####
    cnt = 0
    a = 0
    
    for each in modely:
        a = a + ((modely[cnt] - obsx[cnt])**2)
        cnt += 1
    mean = sum(obsx)/len(obsx)
    rmse = round((a/len(modely))**.5,2)
    nrmse = round(rmse/mean,2)
    print 'RMSE: ' + str(rmse)
    print 'NRMSE: ' + str(nrmse)
    return pbias, mae, ns
    #############################################################################

