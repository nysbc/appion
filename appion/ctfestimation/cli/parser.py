# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import argparse

def constructCTFFindParser():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("-i", "--cs_dir", dest="cryosparc_dir",
        help="Path to CryoSPARC session or job directory.", required=True)
    return parser