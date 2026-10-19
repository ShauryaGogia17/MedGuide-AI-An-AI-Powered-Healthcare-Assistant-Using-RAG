from datetime import date
import numpy as np
from sklearn.linear_model import LinearRegression

def detect_trend(values, dates=None, stable_percent=1.0):
    """Describe direction by elapsed days; the tolerance is descriptive, not clinical."""
    result={'trend':None,'slope':None,'percent_change':None,'slope_unit':'per day' if dates else 'per observation','reason':None}
    if len(values)<2:
        return {**result,'reason':'At least two dated measurements are needed'}
    y=np.asarray(values,dtype=float)
    if not np.isfinite(y).all(): raise ValueError('Measurements must be finite numbers')
    if dates:
        days=np.array([date.fromisoformat(day).toordinal() for day in dates],dtype=float)
        order=np.argsort(days,kind='stable');days=days[order];y=y[order]
        x=days-days[0]
        if len(set(x))<2:return {**result,'reason':'Measurements must span at least two different dates'}
    else:x=np.arange(len(y),dtype=float)
    slope=float(LinearRegression().fit(x.reshape(-1,1),y).coef_[0])
    first=float(y[0]);last=float(y[-1])
    percent=(last-first)/abs(first)*100 if first!=0 else None
    baseline=max(abs(first),abs(last),1e-9)
    fitted_change=abs(slope*(x[-1]-x[0]))/baseline*100
    trend='stable' if fitted_change<=stable_percent else 'increasing' if slope>0 else 'decreasing'
    return {**result,'trend':trend,'slope':slope,'percent_change':percent,'stable_tolerance_percent':stable_percent}
