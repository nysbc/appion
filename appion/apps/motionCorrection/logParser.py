def parseLog(outbuffer: list) -> dict:
    '''
    Parses the output log from motioncor2/motioncor3 and converts it into a dict.
    '''
    logData={}

    # Discard all output before the alignment shifts.
    line=outbuffer.pop(0)
    # For some reason motioncor2 1.6.4 uses a tabular format for the alignment shift outputs, but motioncor3 and older versions of motioncor2 don't.
    # The initial line denoting the shift outputs omits the word "shift".
    while ("Full-frame alignment shift" not in line) and (line.strip() != "Full-frame alignment"):
        if not outbuffer:
            raise RuntimeError("Alignment shift line not found in stdout.")
        line=outbuffer.pop(0)
    line=outbuffer.pop(0)
    logData["shifts"] = []
    while ("Global shifts are corrected" not in line) and outbuffer:
        # Remove empty lines
        if not line and outbuffer:
            line=outbuffer.pop(0)
            continue
        # For some reason motioncor2 1.6.4 uses a tabular format for the alignment shift outputs, but motioncor3 and older versions of motioncor2 don't.
        # This removes a header from that table.
        if "Frame   x Shift   y Shift" in line:
            line=outbuffer.pop(0)
            continue
        try:
            shx = float(line.split()[-2])
            shy = float(line.split()[-1])
            logData["shifts"].append((shx, shy))
        except Exception as e:
            raise RuntimeError("Could not parse shifts in log.  Line: %s" % line) from e
        line=outbuffer.pop(0)
    return logData

def genMotionCorrLog(logData: dict, outputLogPath: str, throw: int, totalRenderedFrames: int, binning: float = 1.0) -> None:
    ''' 
    Takes the output log from motioncor2/motioncor3 and converts it to a motioncorr-formatted log.
    This is necessary because the myamiweb web UI reads motioncorr logs directly / doesn't query the database for information about shifts.
    See here: https://github.com/leginon-org/leginon/blob/34bf9ab9a7a7ec8ae2d9a6ab818a4538cb925787/myamiweb/processing/inc/particledata.inc#L2505-L2533
    '''
    # Convert to the convention used in motioncorr
    # so that shift is in pixels of the aligned image.
    adjusted_shifts = []
    midval = int(len(logData["shifts"])/2)
    midshx = logData["shifts"][midval][0]
    midshy = logData["shifts"][midval][1]
    for shift in logData["shifts"]:
        shxa = -(shift[0] - midshx) / binning
        shya = -(shift[1] - midshy) / binning
        adjusted_shifts.append((shxa, shya))

    # Formats the shifts in motioncorr format.
    with open(outputLogPath,"w") as f:
        f.write("Sum Frame #%.3d - #%.3d (Reference Frame #%.3d):\n" % (0, totalRenderedFrames, totalRenderedFrames/2))
        # Eer nframe is not predictable.
        for idx, adjusted_shift in enumerate(adjusted_shifts):
            f.write("......Add Frame #%.3d with xy shift: %.5f %.5f\n" % (idx+throw, adjusted_shift[0], adjusted_shift[1]))