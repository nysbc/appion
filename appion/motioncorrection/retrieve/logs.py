from typing import Callable

def retrieveLogParser(version : str) -> Callable:
    if version.strip() == "MotionCor2 version 1.6.4":
        # motioncor2 1.6.4 uses a tabular format for the alignment shift outputs, but motioncor3 and older versions of motioncor2 don't.
        # This ensures that shifts are read after the table header.
        return lambda outbuffer : parseMotionCorLog(outbuffer, "Frame   x Shift   y Shift")
    # All other versions of motioncor2/motioncor2 seem to use the same output format.
    return lambda outbuffer : parseMotionCorLog(outbuffer, "Full-frame alignment shift")


def parseMotionCorLog(outbuffer: list, shift_start: str) -> dict:
    '''
    Parses the output log from motioncor2/motioncor3 and converts it into a dict.
    '''
    logData={}

    # Discard all output before the alignment shifts.
    line=outbuffer.pop(0)
    while (shift_start not in line):
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
        try:
            shx = float(line.split()[-2])
            shy = float(line.split()[-1])
            logData["shifts"].append((shx, shy))
        except Exception as e:
            raise RuntimeError("Could not parse shifts in log.  Line: %s" % line) from e
        line=outbuffer.pop(0)
    return logData