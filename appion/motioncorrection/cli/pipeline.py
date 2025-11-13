from .pretask import preTask
from ..calc.external import motioncor, checkImageExists
from .posttask import postTask

def pipeline(imageid: int, args : dict, jobmetadata: dict):
    if checkImageExists(imageid):
        kwargs, imgmetadata=preTask(imageid, args)
        logData, logStdOut=motioncor(**kwargs)
        postTask(imageid, kwargs, imgmetadata, jobmetadata, args, logData, logStdOut)
