from collections import defaultdict
from ml.trend_detector import detect_trend
from ml.anomaly_detector import compare_reference,historical_z_score

def analyze_labs(observations):
    groups=defaultdict(list);undated=0;undated_readings=[]
    for observation in observations:
        if not observation.get('date'):
            undated+=1
            undated_readings.append({**observation,**compare_reference(observation['value'],observation.get('reference_low'),observation.get('reference_high'),observation.get('low_inclusive'),observation.get('high_inclusive'))})
            continue
        key=(' '.join(observation['test_name'].casefold().split()),(observation.get('unit') or '').casefold().strip())
        groups[key].append(observation)
    series=[]
    for points in groups.values():
        points.sort(key=lambda point:(point['date'],point['report_id']))
        previous=[]
        processed=[]
        for point in points:
            processed.append({**point,**compare_reference(point['value'],point.get('reference_low'),point.get('reference_high'),point.get('low_inclusive'),point.get('high_inclusive')),**historical_z_score(point['value'],previous)})
            previous.append(point['value'])
        analysis=detect_trend([p['value'] for p in points],[p['date'] for p in points]) if points[0].get('unit') else {'trend':None,'slope':None,'percent_change':None,'reason':'Units are missing; confirm comparability before interpreting a trend'}
        series.append({'test_name':points[0]['test_name'],'unit':points[0].get('unit'),'points':processed,'analysis':analysis,'latest':processed[-1]})
    series.sort(key=lambda entry:entry['test_name'].casefold())
    return {'series':series,'undated_values':undated,'undated_readings':undated_readings,'note':'Directions and statistical flags are descriptive only. Compare tests with the same units and review laboratory method and reference-range changes with your clinician.'}
