import argparse


def constructCSMotionCorParser():
    parser = argparse.ArgumentParser(add_help=False)

    # Inputs
    parser.add_argument("-i", "--cs_import_dir", dest="cryosparc_import_dir",
        help="Path to CryoSPARC imports directory.", required=True)
    parser.add_argument("-m", "--cs_motioncorrection_dir", dest="cryosparc_motioncorrection_dir",
        help="Path to CryoSPARC motion correction outputs directory.", required=True)
    # Integer
    parser.add_argument("--alignlabel", dest="alignlabel", default='a',
        help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")

    return parser