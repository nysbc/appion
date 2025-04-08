def parseLog(outbuffer: list) -> dict:
    '''
    Parses the output log from ctffind4 and converts it into a dict.
    '''
    logData={}
    for line in outbuffer:
        line = line.strip()
        if line.startswith('#'):
            continue
        columns = line.split()
        if len(columns) < 7:
            raise RuntimeError("Invalid number of columns in ctffind4 log (is %d; should be 7)." % len(columns))
        logData = {
            'micrograph_number': int(float(columns[0])),
            'defocus_1': float(columns[1]),
            'defocus_2': float(columns[2]),
            'azimuth_of_astigmatism;':	float(columns[3]),
            'additional_phase_shift':	float(columns[4]), # radians
            'cross_correlation':	float(columns[5]),
            'spacing':	float(columns[6])
        }
    if not logData:
        raise RuntimeError("No data was found in log.")
    return logData
    
def genAppionLog(logData : dict, ampcontrast: float, bestdef: float, cs: float, volts: float) -> dict:
    appionLogData = {
        'imagenum': logData["micrograph_number"],
        'defocus2':	logData["defocus_2"]*1e-10,
        'defocus1':	logData["defocus_1"]*1e-10,
        'angle_astigmatism':	logData["azimuth_of_astigmatism"]+90, # see bug #4047 for astig conversion
        'extra_phase_shift':	logData["additional_phase_shift"], # radians
        'amplitude_contrast': ampcontrast,
        'cross_correlation':	logData["cross_correlation"],
        'ctffind4_resolution':	logData["spacing"] if logData["spacing"] != float("inf") else 100000.0,
        'defocusinit':	bestdef*1e-10,
        'cs': cs,
        'volts': volts,
        'confidence': logData["cross_correlation"],
        'confidence_d': round(abs(float(logData["cross_correlation"]))**(1/2), 5)
    }
    return appionLogData