
def pipeline(batchid: int, imageids: int, args : dict, jobmetadata: dict):
    # Sinedon needs to be reimported and setup within the local scope of this function
    # because the function runs in a forked process
    # that doesn't have Django initialized.
    import sinedon.setup
    sinedon.setup(args['projectid'], False)
    from .pretask import preTask
    from ..calc.external import motioncor, checkImageExists
    from .posttask import postTask
    import os
    image_pretask_results={}
    batchdir=os.path.join(args["run_dir"],"batch-%d" % batchid)
    if not os.path.isdir(batchdir):
        os.makedirs(batchdir)
    for imageid in imageids:
        if checkImageExists(imageid):
            kwargs, imgmetadata=preTask(imageid, args)
            image_pretask_results[imageid]={}
            image_pretask_results[imageid]['kwargs']=kwargs
            image_pretask_results[imageid]['imgmetadata']=imgmetadata
    kwargs, image_pretask_results=construct_serial_kwargs(image_pretask_results, args, batchdir)
    logData, logStdOut=motioncor(**kwargs)
    for imageid in image_pretask_results.keys():
        postTask(imageid, image_pretask_results[imageid]['kwargs'], image_pretask_results[imageid]['imgmetadata'], jobmetadata, args, logData, logStdOut)

def construct_serial_kwargs(image_pretask_results, args, batchdir):
    import os
    from ..calc.internal import calcImageDefectMap
    from ..store import saveDefectMrc, saveDark, saveFmIntFile
    kwargs={}
    merged_darks={}
    merged_fmintfiles={}
    merged_defect_maps={}
    for imageid in image_pretask_results.keys():
        # Dark inputs
        ccdcamera_id=0
        cameraemdata_id=0
        darkmetadata_darkimagedata_id=0
        darkmetadata_sessiondata_id=0
        if image_pretask_results["imgmetadata"]["ccdcamera"]:
            if "def_id" in image_pretask_results["imgmetadata"]["ccdcamera"].keys():
                ccdcamera_id=image_pretask_results["imgmetadata"]["ccdcamera"]["def_id"]
        if image_pretask_results["imgmetadata"]["cameraemdata"]:
            if "def_id" in image_pretask_results["imgmetadata"]["cameraemdata"].keys():
                cameraemdata_id=image_pretask_results["imgmetadata"]["cameraemdata"]["def_id"]
        if image_pretask_results["imgmetadata"]['darkmetadata']:
            if image_pretask_results["imgmetadata"]['darkmetadata']['darkimagedata']:
                if "def_id" in image_pretask_results["imgmetadata"]['darkmetadata']['darkimagedata'].keys():
                    darkmetadata_darkimagedata_id=image_pretask_results["imgmetadata"]['darkmetadata']['darkimagedata']['def_id']
            if image_pretask_results["imgmetadata"]['darkmetadata']['sessiondata']:
                if "def_id" in image_pretask_results["imgmetadata"]['darkmetadata']['sessiondata'].keys():
                    darkmetadata_sessiondata_id=image_pretask_results["imgmetadata"]['darkmetadata']['sessiondata']["def_id"]
        dark_unique_id="ccd-%d_cameraem-%d_image-%d_session-%d" % (ccdcamera_id, cameraemdata_id, darkmetadata_darkimagedata_id, darkmetadata_sessiondata_id)
        if dark_unique_id not in merged_darks.keys():
            merged_darks[dark_unique_id]={}
            merged_darks[dark_unique_id]["kwargs"]={}
            merged_darks[dark_unique_id]["kwargs"]["dark_output_path"]=os.path.join(batchdir,"dark-%s.mrc" % dark_unique_id)
            merged_darks[dark_unique_id]["kwargs"]["camera_name"]=image_pretask_results["imgmetadata"]["ccdcamera"]['name']
            merged_darks[dark_unique_id]["kwargs"]["eer_frames"]=image_pretask_results["imgmetadata"]['cameraemdata']['eer_frames']
            merged_darks[dark_unique_id]["kwargs"]["dark_input_path"]=image_pretask_results["imgmetadata"]["dark_input"]
            merged_darks[dark_unique_id]["kwargs"]["nframes"]=image_pretask_results["imgmetadata"]['darkmetadata']['cameraemdata']["nframes"]
            merged_darks[dark_unique_id]["images"]=set()
        merged_darks[dark_unique_id]["images"].add(imageid)
        image_pretask_results["kwargs"]["Dark"]=merged_darks[dark_unique_id]["kwargs"]["dark_output_path"]

        # FmIntFile inputs
        fmintfile_unique_id="cameraem-%d_framesize-%d_fmdose-%d" % (cameraemdata_id, args['rendered_frame_size'], image_pretask_results["kwargs"]["FmDose"])
        if fmintfile_unique_id not in merged_fmintfiles.keys():
            merged_fmintfiles[fmintfile_unique_id]={}
            merged_fmintfiles[fmintfile_unique_id]["kwargs"]={}
            merged_fmintfiles[fmintfile_unique_id]["kwargs"]["fmintpath"]=os.path.join(batchdir,"fmintfile-%s.txt" % fmintfile_unique_id)
            merged_fmintfiles[fmintfile_unique_id]["kwargs"]["nraw"]=image_pretask_results["imgmetadata"]['cameraemdata']['nframes']
            merged_fmintfiles[fmintfile_unique_id]["kwargs"]["size"]=args['rendered_frame_size']
            merged_fmintfiles[fmintfile_unique_id]["kwargs"]["raw_dose"]=image_pretask_results["kwargs"]["FmDose"] / args['rendered_frame_size']
            merged_fmintfiles[fmintfile_unique_id]["images"]=set()
        merged_fmintfiles[fmintfile_unique_id]["images"].add(imageid)

        # Defect Map inputs
        correctorplan_id=0
        if image_pretask_results["imgmetadata"]["correctorplandata"]:
            if "def_id" in image_pretask_results["imgmetadata"]["correctorplandata"].keys():
                correctorplan_id=image_pretask_results["imgmetadata"]["correctorplandata"]["def_id"]
        defect_map_unique_id="cameraem-%d_correctorplan-%d" % (cameraemdata_id, correctorplan_id)
        if defect_map_unique_id not in merged_defect_maps.keys():
            defect_map=calcImageDefectMap(image_pretask_results["imgmetadata"]["correctorplandata"]['bad_rows'], 
                                        image_pretask_results["imgmetadata"]["correctorplandata"]['bad_cols'], 
                                        image_pretask_results["imgmetadata"]["correctorplandata"]['bad_pixels'], 
                                        image_pretask_results["imgmetadata"]['cameraemdata']["subd_dimension_x"], 
                                        image_pretask_results["imgmetadata"]['cameraemdata']["subd_dimension_y"], 
                                        image_pretask_results["imgmetadata"]['cameraemdata']['frame_flip'], 
                                        image_pretask_results["imgmetadata"]['cameraemdata']['frame_rotate'])
            merged_defect_maps[defect_map_unique_id]["kwargs"]={}
            merged_defect_maps[defect_map_unique_id]["kwargs"]["defect_map_path"]=os.path.join(batchdir,"defectmap-%s.mrc" % defect_map_unique_id)
            merged_defect_maps[defect_map_unique_id]["kwargs"]["defect_map"]=defect_map

        
    for merged_dark in merged_darks.keys():
        if not os.path.exists(merged_darks[merged_dark]["kwargs"]["dark_output_path"]):
            saveDark(**merged_darks[merged_dark]["kwargs"])
    for merged_fmintfile in merged_fmintfiles.keys():
        if not os.path.exists(merged_fmintfiles[merged_fmintfile]["kwargs"]["fmintpath"]):
            saveFmIntFile(**merged_fmintfiles[merged_fmintfile]["kwargs"])
    for merged_defect_map in merged_defect_maps.keys():
        if not os.path.exists(merged_defect_maps[merged_defect_map]["kwargs"]["defect_map_path"]):
            saveDefectMrc(**merged_defect_maps["kwargs"])
    return kwargs, image_pretask_results