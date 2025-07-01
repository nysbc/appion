import os
import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata
import mrcfile
import numpy
from glob import glob

for idx, mrc in enumerate(glob(os.path.join(os.getcwd(),"*.mrc"))):
    imageid=os.path.splitext(os.path.basename(mrc))[0]
    imgmetadata=readImageMetadata(imageid, True)
    defect_map_args=(imgmetadata['bad_rows'], imgmetadata['bad_cols'], imgmetadata['bad_pixels'], imgmetadata['dx'], imgmetadata['dy'])
    defect_map=mrcfile.read(mrc)
    numpy.savez_compressed("./test_motioncorrection_defect_map_%d.npz" % idx, defect_map=defect_map, defect_map_args=defect_map_args)