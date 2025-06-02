import argparse
import os

def constructGlobalParser():
    """
    Function that adds universal Appion options to an ArgumentParser object.
    """
    parser = argparse.ArgumentParser(add_help=False)

    ### Input value options
    parser.add_argument("-R", "--rundir", "--outdir", dest="rundir",
        help="Run path for storing output, e.g. --rundir=/data/appion/runs/run1", default=os.getcwd())
    parser.add_argument("-s", "--session", dest="sessionname",
        help="Session name associated with processing run, e.g. --session=06mar12a")
    parser.add_argument("--preset", dest="preset",
        help="Image preset associated with processing run, e.g. --preset=en")
    parser.add_argument("--clusterconfig", dest="clusterconfig",
        help="Path to a YAML file that contains Dask cluster configuration info.", type=str, default="/etc/dask/cluster.yml")

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
    parser.add_argument("--no-rejects", dest="rejects", default=False,
        action="store_false", help="Do not process hidden or rejected images")
    parser.add_argument("--reverse", dest="reverse", default=False,
        action="store_true", help="Process the images from newest to oldest")
    parser.add_argument("--parallel", dest="parallel", default=False,
        action="store_true", help="parallel appionLoop on different cpu. Only work with the part not using gpu")
    
    parser.add_argument("-n", "--runname", dest="runname",
        help="Name for processing run, e.g. --runname=run1")
    parser.add_argument("-d", "--description", dest="description",
        help="Description of the processing run (must be in quotes)")
    parser.add_argument("-p", "--projectid", dest="projectid", type=int,
        help="Project id associated with processing run, e.g. --projectid=159")
    parser.add_argument("-C", "--commit", dest="commit", default=True,
        action="store_true", help="Commit processing run to database")
    parser.add_argument("--no-commit", dest="commit", default=True,
        action="store_false", help="Do not commit processing run to database")

    parser.add_argument("--expid", "--expId", dest="expid", type=int,
        help="Session id associated with processing run, e.g. --expid=7159")
    parser.add_argument("--nproc", dest="nproc", type=int,
        help="Number of processor to use")
    return parser