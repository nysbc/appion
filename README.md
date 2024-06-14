# SEMC Appion/SLURM Fork

This repository consists of a fork of Appion that is intended specifically for use with the SLURM cluster at SEMC.  Its primary function is to accurately reflect the minimum functionality needed for SEMC's everyday operations.  Stated differently, only the applications that microscope operators regularly run are supported, and all other applications are removed.  If an application needs to be re-added to this repository from the main Leginon repository this will be done on an as-needed basis.  Our primary goal/strategy here is to maintain a slimmed down version of Appion to which features that are no longer commonly used can be re-added gradually.

## Web Forms

The following `myamiweb` web forms (found under `myamiweb/processing/inc/forms`) are supported by / functional with this fork of Appion:

```
./ctfFind4.inc
./motioncor2_ucsf.inc
./gctf.inc
./dogPickerForm.inc
./dogPicker2Form.inc
```

The following web forms are not supported:

```
./manualPickerForm.inc
./protomo2RefineSummary.inc
./protomo2BatchSummary.inc
./fibsem_AlignStackForm.inc
./deParticleAlignForm.inc
./fibsem_ClipStackForm.inc
./uploadExternalRefine.inc
./gautomatchForm.inc
./makeDEAlignedSum.inc
./protomo2CoarseAlignForm.inc
./relion2Align2D_AWS_Form.inc
./topazDenoiser.inc
./quickStackForm.inc
./fibsem_MakeStackForm.inc
./learningStackCleaner.inc
./dBMaskAutoMaskForm.inc
./xmipp3CL2DAlign.inc
./protomo2RefineForm.inc
./isacForm.inc
./deleteHidden.inc
./protomo2CoarseAlignSummary.inc
./rubinsteinParticlePolisher.inc
./launchFrameTransfer.inc
./fibsem_GenerateStackForm.inc
./MotionCorrPurdueForm.inc
./uploadCtf.inc
./uploadRelion3DRefineForm.inc
./imgRejector2Form.inc
./relion2Align2DForm.inc
./fibsem_DewarpStackForm.inc
./autoMaskForm.inc
./makeDDStackForm.inc
./templatePickerForm.inc
./protomo2ReconstructionForm.inc
./protomo2UploadForm.inc
./generateMissingStackForm.inc
./makeDEPerParticle.inc
./replaceRelion2DRefs.inc
./transferCtf.inc
./protomo2TomoCTFEstimate.inc
./relionAlign2DForm.inc
./protomo2BatchForm.inc
```

## Required Appion Executables for Supported Forms

```
./ctfFind4.inc:         $this->setExeFile( 'ctffind4.py' );
./motioncor2_ucsf.inc:          $this->setExeFile( 'makeDDAlignMotionCor2_UCSF.py' );
./gctf.inc:             $this->setExeFile( 'gctf.py' );
./dogPickerForm.inc:            $this->setExeFile( 'dogPicker.py' );
./dogPicker2Form.inc:           $this->setExeFile( 'dogPicker2.py' );
./manualPickerForm.inc:         $this->setExeFile( 'manualpicker.py' );
```

`updateAppionDB.py` is also required for SLURM jobs, as this runs at the end of an Appion job.

## Required Appion Libraries for Supported Appion Executables

```
appionlib.apAppionCamProcess
appionlib.apCrud
appionlib.apCtf.ctfdb
appionlib.apCtf.ctfdisplay
appionlib.apCtf.ctffind4AvgRotPlot
appionlib.apCtf.ctfinsert
appionlib.apCtf.ctfnoise
appionlib.apCtf.ctfpower
appionlib.apCtf.ctfres
appionlib.apCtf.ctftools
appionlib.apCtf.genctf
appionlib.apDatabase
appionlib.apDBImage
appionlib.apDDAlignStackMaker
appionlib.apDDFrameAligner
appionlib.apDDLoop
appionlib.apDDMotionCorrMaker
appionlib.apDDprocess
appionlib.apDDResult
appionlib.apDDStackMaker
appionlib.apDefocalPairs
appionlib.apDEprocess
appionlib.apDisplay
appionlib.apDog
appionlib.apEerProcess
appionlib.apFalcon2Process
appionlib.apFalcon3Process
appionlib.apFile
appionlib.apImage
appionlib.apImage.imagefile *
appionlib.apImage.imagefilter *
appionlib.apImage.imagenorm *
appionlib.apImage.imagestat *
appionlib.apImage.onedimfilter *
appionlib.apSpider *
appionlib.apInstrument
appionlib.apK2process
appionlib.apMask
appionlib.apParam
appionlib.apParticle
appionlib.apPeaks
appionlib.appiondata
appionlib.appionLoop2
appionlib.appionScript
appionlib.apProject
appionlib.apRelion
appionlib.apScriptLog
appionlib.apSimFrameProcess
appionlib.apStack
appionlib.apThread
appionlib.apWebScript
appionlib.basicScript
appionlib.filterLoop
appionlib.particleLoop2
appionlib.processingHost
appionlib.slurmHost
appionlib.StackClass.stackTools
appionlib.StackClass.ProcessStack
appionlib.StackClass.mrcClass
appionlib.StackClass.hdfClass
appionlib.StackClass.imagicClass
appionlib.StackClass.baseClass
appionlib.starFile
appionlib.apImagicFile
appionlib.pymagic

* Spider dependency, but Spider seems to be a dead project.
```
