import argparse

def constructCTFFindParser():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--ampcontrast", dest="ampcontrast", type=float, default=0.07,
        help="ampcontrast, default=0.07")
    parser.add_argument("--fieldsize", dest="fieldsize", type=int, default=1024,
        help="fieldsize, default=1024")
    parser.add_argument("--nominal", dest="nominal", type=float,
        help="nominal override value (in microns, absolute value)")
    parser.add_argument("--resmin", dest="resmin", type=float, default=50.0,
        help="Low resolution end of data to be fitted in Angstroms")
    parser.add_argument("--resmax", dest="resmax", type=float, default=15.0,
        help="High resolution end of data to be fitted in Angstroms")
    parser.add_argument("--defstep", dest="defstep", type=float, default=1000.0,
        help="Step width for grid search in microns")
    parser.add_argument("--numstep", dest="numstep", type=int, default=25,
        help="Number of steps to search in grid")
    parser.add_argument("--dast", dest="dast", type=float, default=100.0,
        help="dAst in microns is used to restrain the amount of astigmatism")
    parser.add_argument("--minphaseshift", "--min_phase_shift", dest="min_phase_shift", type=float, default=10.0,
        help="Minimum phase shift by phase plate, in degrees")
    parser.add_argument("--maxphaseshift", "--max_phase_shift", dest="max_phase_shift", type=float, default=170.0,
        help="Maximum phase shift by phase plate, in degrees")
    parser.add_argument("--phasestep", "--phase_search_step", dest="phase_search_step", type=float, default=10.0,
        help="phase shift search step, in degrees")
    parser.add_argument("--ddstackid", dest="ddstackid",type=int, help="DD stack ID")
    parser.add_argument("--num_frame_avg", dest="num_frame_avg", type=int, default=7,
        help="Average number of moive frames for movie stack CTF refinement")


    ## true/false
    parser.add_argument("--bestdb", "--best-database", dest="bestdb", default=False,
        action="store_true", help="Use best amplitude contrast and astig difference from database")
    parser.add_argument("--phaseplate", "--phase_plate", dest="shift_phase", default=False,
        action="store_true", help="Find additionalphase shift")
    parser.add_argument("--exhaust", "--exhaustive-search", dest="exhaustiveSearch", default=False,
        action="store_true", help="Conduct an exhaustive search of the astigmatism of the CTF")