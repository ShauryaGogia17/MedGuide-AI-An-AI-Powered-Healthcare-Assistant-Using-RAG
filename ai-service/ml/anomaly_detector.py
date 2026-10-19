import numpy as np

def compare_reference(value,low=None,high=None,low_inclusive=True,high_inclusive=True):
    if low is None and high is None: return {'out_of_range':False,'range_status':'reference unavailable'}
    below=low is not None and (value<low if low_inclusive is not False else value<=low)
    above=high is not None and (value>high if high_inclusive is not False else value>=high)
    return {'out_of_range':bool(below or above),'range_status':'out of range' if below or above else 'within reference range'}

def historical_z_score(value,previous_values,min_history=8):
    """Use earlier readings only. A statistical flag never implies a disease."""
    if len(previous_values)<min_history: return {'z_score':None,'statistical_anomaly':False}
    baseline=np.asarray(previous_values,dtype=float)
    deviation=float(np.std(baseline,ddof=1))
    if deviation<1e-9:return {'z_score':None,'statistical_anomaly':False}
    score=float((value-float(np.mean(baseline)))/deviation)
    return {'z_score':score,'statistical_anomaly':abs(score)>3}
