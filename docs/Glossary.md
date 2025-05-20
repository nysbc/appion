# Cryo-EM Glossary: An Aid for Mere Mortals, Lay(wo)men, and Peasants

* Grid: A metal (often copper) disk with a mesh patchwork that creates a matrix.  Sample proteins are placed within the matrix cells and imaged.  Essentially grids are to electron microscopy what slides are to light microscopy.
* Square: Refers to a cell in a grid.  Squares have holes within them, which form another matrix.  Samples concentrate within holes.  Squares are essentially a sub-matrix.
* Hole: A circular cell within a square.  Regions of interest (ROIs) within a hole are imaged with the highest possible magnification.
* Atlas: A composite image that consists of multiple images of the grid that have been tiled together.  The component images are zoomed out.  An atlas provides a comprehensive view of the whole grid.  It is used to find regions of interest (ROIs), which within this context are promising squares for imaging at higher resolutions.

* Movie: A time series recording of electrons as they hit the microscope detector.
* Frame: An individual time point in the movie.  Encoded as a sparse image of binary bits.
* Micrograph: A magnified image of an object.  Within the context of Cryo-EM, a micrograph is defined as the sum of a number of motion-corrected frames.  Micrographs are the outputs of motion correction commands, such as `motioncor2`/`motioncor3`, while frames are the input.  Micrographs are stored with 16 bit precision.
* Patches: Multiple bounded areas within a frame that are aligned using patch-based motion correction.  Patches can be viewed as indices within a frame.  Local (patch-based) motion correction is preferred to global (whole frame) motion correction.
* Gain: An image taken without a sample.  Gains are used to calibrate processing and remove artifacts from images that are due to the variable sensitivities 