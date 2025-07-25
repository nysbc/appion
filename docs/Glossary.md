# Cryo-EM Glossary: An Aid for Mere Mortals, Lay(wo)men, and Peasants

* Grid: A metal (often copper) disk with a mesh patchwork that creates a matrix.  Sample proteins are placed within the matrix cells and imaged.  Essentially grids are to electron microscopy what slides are to light microscopy.
* Square: Refers to a cell in a grid.  Squares have holes within them, which form another matrix.  Samples concentrate within holes.  Squares are essentially a sub-matrix.
* Hole: A circular cell within a square.  Regions of interest (ROIs) within a hole are imaged with the highest possible magnification.
* Atlas: A composite image that consists of multiple images of the grid that have been tiled/stitched together.  The component images are zoomed out.  An atlas provides a comprehensive view of the whole grid.  It is used to find regions of interest (ROIs), which within this context are promising squares for imaging at higher resolutions.

* Movie: A time series recording of electrons as they hit the microscope detector.
* Frame / Exposure: An individual time point in the movie.  Encoded as a sparse image of binary bits.
* Stacking: In general microscopy, the act of combining multiple images acquired at different focus points into a single image with more detail than can be provided by any individual image alone.
* Micrograph: A magnified image of an object.  Within the context of Cryo-EM, a micrograph is often synonymous with a set of frames that have been stacked into an individual image (via summation).   Micrographs are stored with 16 bit precision.  Micrographs are the outputs of motion correction commands, such as `motioncor2`/`motioncor3`, while frames/frame stacks are the input.
* Frame Stack: A collection of frames that have been acquired using different focus settings.  Frame stacks are gain-corrected, dark-corrected, aligned, averaged, and (optionally) dose-weighted to create micrographs. 
* Frame Aligner: A program/function that is used to align objects within a frame stack.  Frame aligner functionality is part of `motioncor2` and CryoSPARC's patch-based motion correction.
* Patches: Multiple bounded areas within a frame that are aligned using patch-based motion correction.  Patches can be viewed as indices within a frame.  Local (patch-based) motion correction is preferred to global (whole frame) motion correction.
* Gain Image: An image taken without a sample.  Gains are used to calibrate processing and remove artifacts from images that are due to the variable sensitivities of different direct detectors / cameras.
* Dark Image: TODO
* Dose Weighting: A preprocessing technique in which different time points in a movie (i.e., different frames) are weighted differently when combined into a micrograph.  Varying the influence of a particular time point on the final image is necessary because the longer electrons bombard the sample, the more damage is done to it.  Applying different weights to different time points allows us to account for this damage.
* Particle Stack: A collection of images of individual particles.  Images in this collection are derived from a micrograph / frame stack.  Particle images are cropped from the micrograph using a square bounding box.  A stack is the input to a 2d classifier (for refinedment) or 3d reconstruction.
* Particle Class: A collection of images of particles that are in the same orientation.  Derived from a stack (a one-to-many mapping).  Used to sort out junk data from useful data and as a measure of quality control (more classes signifies more orientations, which indicates better data with which to infer the 3d structure of a protein).

* Contrast Transfer Function (CTF): A wave function that is used to adjust image contrast.  This correction is necessary due to the natural distortions of a projected image that cause contrast to be distributed unevenly.


* Direct Detector (camera) : The sensor used to record electrons as they are deflected by the sample that is being imaged.  See [here](https://en.wikipedia.org/wiki/Detectors_for_transmission_electron_microscopy#Direct_electron_detectors).  Common brands include Gatan and Falcon (ThermoFisher Scientific).

## More Resources:

* https://cryoem101.org/chapter-5/
* https://cryoedu.org/chapter-1/
* https://guide.cryosparc.com/processing-data/all-job-types-in-cryosparc/motion-correction
* https://guide.cryosparc.com/processing-data/all-job-types-in-cryosparc/ctf-estimation
* https://cryo-em-course.caltech.edu/
* https://www.quekett.org/resources/stacking-and-stitching/stacking
* https://spider-em.github.io/SPIDER/docs/glossary.html