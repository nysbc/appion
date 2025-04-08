def parseLog(outbuffer: list, motionCorVersion: str = "2.1.5.0") -> dict:
    '''
    Parses the output log from motioncor2/motioncor3 and converts it into a dict.
    '''
    logData={}
    # Convert semantic version to int.  Use a dummy version if the version can't be cast into a float.
    try:
        motionCorVersion=motionCorVersion.split(".")
        motionCorVersion=float("".join(motionCorVersion))/(10**(len(motionCorVersion)-1))
    except:
        motionCorVersion=0.0

    # Discard all output before the alignment shifts.
    line=outbuffer.pop()
    while "Full-frame alignment shift" not in line:
        if not outbuffer:
            raise RuntimeError("Alignment shift line not found in stdout.")
        line=outbuffer.pop()
    logData["shifts"] = []
    while ("Global shifts are corrected" not in line) and outbuffer:
        # Remove empty lines
        while not line and outbuffer:
            line=outbuffer.pop()
        # For some reason motioncor2 1.6.4 uses a tabular format for the alignment shift outputs, but motioncor3 and older versions of motioncor2 don't.
        # This logic is meant to deal with that edge case.
        if "Frame   x Shift   y Shift" in line and motionCorVersion == 2.164:
            line=outbuffer.pop()
        if line.startswith("...... Frame") or motionCorVersion == 2.164:
            try:
                shx = float(line.split()[-2])
                shy = float(line.split()[-1])
                logData["shifts"].append((shx, shy))
            except Exception as e:
                raise RuntimeError("Could not parse shifts in log.") from e
        line=outbuffer.pop()
    return logData

def genMotionCor1Log(logData: dict, logPath: str, throw: int, totalRenderedFrames: int, binning: float = 1.0) -> None:
    ''' 
    Takes the output log from motioncor2/motioncor3 and converts it to a motioncor1-formatted log.
    This is necessary because the myamiweb web UI reads motioncor1 logs directly / doesn't query the database for information about shifts.
    See here: https://github.com/leginon-org/leginon/blob/34bf9ab9a7a7ec8ae2d9a6ab818a4538cb925787/myamiweb/processing/inc/particledata.inc#L2505-L2533
    '''
    # Convert motioncor2 output to motioncor1 format
    adjusted_shifts = []
    midval = len(logData["shifts"])/2
    midshx = logData["shifts"][midval][0]
    midshy = logData["shifts"][midval][1]
    for shift in logData["shifts"]:
        # Convert to the convention used in motioncorr
        # so that shift is in pixels of the aligned image.
        shxa = -(shift[0] - midshx) / binning
        shya = -(shift[1] - midshy) / binning
        adjusted_shifts.append((shxa, shya))

    # motioncorr1 format, needs conversion from motioncorr2 format
    with open(logPath,"w") as f:
        f.write("Sum Frame #%.3d - #%.3d (Reference Frame #%.3d):\n" % (0, totalRenderedFrames, totalRenderedFrames/2))
        # Eer nframe is not predictable.
        for idx, adjusted_shift in enumerate(adjusted_shifts):
            f.write("......Add Frame #%.3d with xy shift: %.5f %.5f\n" % (idx+throw, adjusted_shift[0], adjusted_shift[1]))