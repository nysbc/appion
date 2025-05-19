import argparse
import os

def constructGlobalParser():
    """
    Function that adds universal Appion options to an ArgumentParser object.
    """
    parser = argparse.ArgumentParser(add_help=False)

    ### Input value options
    parser.add_argument("-r", "--rundir", dest="rundir",
        help="Path to the run directory", type=str, default=os.getcwd())
    parser.add_argument("-s", "--session", dest="sessionname",
        help="Session name associated with processing run, e.g. --session=06mar12a")
    parser.add_argument("--preset", dest="preset",
        help="Image preset associated with processing run, e.g. --preset=en")

    #parser.add_argument("--reprocess", dest="reprocess", type=float,
    #	help="Only process images that pass this reprocess criteria")

    tiltoptions = ("notilt", "hightilt", "lowtilt", "minustilt", "plustilt", "all")
    parser.add_argument("--tiltangle", dest="tiltangle", 
        default="all", choices=tiltoptions,
        help="Only process images with specific tilt angles, options: "+str(tiltoptions))

    ### True / False options
    parser.add_argument("--continue", dest="continue", default=True,
        action="store_true", help="Continue processing run from last image")
    #parser.add_argument("--no-continue", dest="continue", default=True,
    #	action="store_false", help="Do not continue processing run from last image")
    parser.add_argument("--no-wait", dest="wait", default=True,
        action="store_false", help="Do not wait for more images after completing loop")
    parser.add_argument("--no-rejects", dest="norejects", default=False,
        action="store_true", help="Do not process hidden or rejected images")
    parser.add_argument("--reverse", dest="reverse", default=False,
        action="store_true", help="Process the images from newest to oldest")
    parser.add_argument("--parallel", dest="parallel", default=False,
        action="store_true", help="parallel appionLoop on different cpu. Only work with the part not using gpu")
    return parser