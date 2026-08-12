import argparse


def constructCSMotionCorParser():
    parser = argparse.ArgumentParser(add_help=False)

    # Inputs
    parser.add_argument("-p", "--cs_project", dest="cryosparc_project",
        help="CryoSPARC project number (integer).", type=int, required=True)
    parser.add_argument("-s", "--cs_session", dest="cryosparc_session",
        help="CryoSPARC live session number (integer).", type=int, required=True)
    # Integer
    parser.add_argument("--alignlabel", dest="alignlabel", default='a',
        help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")

    return parser
