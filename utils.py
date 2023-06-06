import pandas as pd
def saveData(_plt, scantype, datdir):
    X = _plt.getCurve(legend='pos').getData()[0]
    pos = _plt.getCurve(legend='pos').getData()[1]
    neg = _plt.getCurve(legend='neg').getData()[1]
    diff = _plt.getCurve(legend='diff').getData()[1]
    err_diff =  _plt.getCurve(legend='diff').getData()[3]

    unit = "[eV]"*(scantype=='energy') + "[ps]"*(scantype=='delay')
    measurement = _plt.getGraphTitle()
    _scan = "xas"*(scantype=='energy') + "delay"*(scantype=='delay')
    
    pd.DataFrame(
        {
            'X {:s}'.format(unit): X,
         'pos': pos,
            'neg': neg,
            'diff': diff,
         'err_diff': err_diff
        }
        )[['X {:s}'.format(unit),'pos','neg','diff','err_diff']].to_csv(datdir+'/'+"{:s}_{:s}.csv".format(measurement, _scan),index=False)
