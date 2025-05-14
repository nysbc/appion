import argparse

def constructMotionCorParser():
    parser = argparse.ArgumentParser(add_help=False)
    # Integer
    parser.add_argument("--ddstartframe", dest="startframe", type=int, default=0,
        help="starting frame for summing the frames. The first frame is 0")
    parser.add_argument("--alignlabel", dest="alignlabel", default='a',
        help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")
    parser.add_argument("--bin",dest="bin",type=float,default="1.0",
        help="Binning factor relative to the dd stack. MotionCor2 takes float value (optional)")

    # Dosefgpu_driftcoor options
    parser.add_argument("--alignoffset", dest="fod", type=int, default=2,
        help="number of frame offset in alignment in dosefgpu_driftcorr")
    parser.add_argument("--alignccbox", dest="pbx", type=int, default=128,
        help="alignment CC search box size in dosefgpu_driftcorr")

    # Dose weighting, based on Grant & Grigorieff eLife 2015
    parser.add_argument("--doseweight",dest="doseweight", default=False,
        action="store_true", help="dose weight the frame stack, according to Tim / Niko's curves")
    parser.add_argument("--totaldose",dest="totaldose", type=float,
                    help="total dose for the full movie stack in e/A^2. If not specified, will get value from database")

    #parser.add_argument("--override_db", dest="override_db", default=False,
    #	action="store_true", help="Override database for bad rows, columns, and image flips")
    # String

    # Integer


    parser.add_argument("--trim", dest="trim", type=int, default=0,
        help="Trim edge off after frame stack gain/dark correction")
    parser.add_argument("--align", dest="align", default=False,
        action="store_true", help="Make Aligned frame stack")

    parser.add_argument("--gpuid", dest="gpuid", type=int, default=0,
        help="GPU device id used in gpu processing")

    parser.add_argument("--gpuids", dest="gpuids", default='0')
    parser.add_argument("--nrw", dest="nrw", type=int, default=1,
        help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")

    parser.add_argument("--FmRef", dest="FmRef",type=int,default=0,
        help="Specify which frame to be the reference to which all other frames are aligned. Default 0 is aligned to the first frame, other values aligns to the central frame.")

    parser.add_argument("--Iter", dest="Iter",type=int,default=7,
        help="Maximum iterations for iterative alignment, default is 7.")

    parser.add_argument("--Tol", dest="Tol",type=float,default=0.5,
                    help="Tolerance for iterative alignment, in pixels")

    parser.add_argument("--Patchrows",dest="Patchrows",type=int,default="0",
        help="Number of patches divides the y-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

    parser.add_argument("--Patchcols",dest="Patchcols",type=int,default="0",
        help="Number of patches divides the x-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

    parser.add_argument("--MaskCentrow",dest="MaskCentrow",type=int,default="0",
        help="Y Coordinates for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

    parser.add_argument("--MaskCentcol",dest="MaskCentcol",type=int,default="0",
        help="X Coordinate for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

    parser.add_argument("--MaskSizecols",dest="MaskSizecols",type=float,default="1.0",
        help="The X size of subarea that will be used for alignment, default 1.0 1.0 corresponding full size.")
    parser.add_argument("--MaskSizerows",dest="MaskSizerows",type=float,default="1.0",
        help="The Y size of subarea that will be used for alignment, default 1.0 corresponding full size.")

    # instead of single align bfactor, bft, this has two entries
    parser.add_argument("--Bft_global",dest="Bft_global",type=float,default=500.0,
                    help=" Global B-Factor for alignment, default 500.0.")

    parser.add_argument("--Bft_local",dest="Bft_local",type=float,default=150.0,
                    help=" Global B-Factor for alignment, default 150.0.")

    #parser.add_argument("--force_cpu_flat", dest="force_cpu_flat", default=False,
    #	action="store_true", help="Use cpu to make frame flat field corrrection")

    parser.add_argument("--rendered_frame_size", dest="rendered_frame_size", type=int, default=1,
        help="Sum this number of saved frames as a rendered frame in alignment", metavar="INT")
    parser.add_argument("--eer_sampling", dest="eer_sampling", type=int, default=1,
        help="Upsampling eer frames. Fourier binning will be added to return the results back", metavar="INT")
    return parser