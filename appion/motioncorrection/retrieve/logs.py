
#TODO create multiple implementations of parseMotionCorLog and return them with a switch.
def retrieveLogParser(version : str) -> function:
    return parseMotionCorLog

def parseMotionCorLog(outbuffer: list) -> dict:
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