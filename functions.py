import numpy as np
from silx.gui.plot import Plot1D

def avg(_plt):
    delay, pos, _, _, _ = _plt.getCurve(legend='pos')
    delay, neg, _, _, _ = _plt.getCurve(legend='neg')
    
    plot1d = Plot1D()
    if len(delay)%2 == 0:
        n = int(len(delay)/2)
        pos_avg = pos[:n]+pos[n:][::-1]
        neg_avg = neg[:n]+neg[n:][::-1]
    elif len(delay)%2 == 1:
        n = int((len(delay)-1)/2)
        pos_avg = pos[:n]+pos[n+1:][::-1]
        neg_avg = neg[:n]+neg[n+1:][::-1]
    plot1d.addCurve(delay[:n],pos_avg,legend='pos')
    plot1d.addCurve(delay[:n],neg_avg,legend='neg')
    plot1d.addCurve(delay[:n],pos_avg-neg_avg,legend='diff',yaxis='right')
    return plot1d
