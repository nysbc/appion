# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

def checkImageExists(imageid: int):
    import sinedon.base as sb
    from ..retrieve.params import readInputPath
    imgdata=sb.get("AcquisitionImageData",{"def_id":imageid})
    sessiondata=sb.get("SessionData",{"def_id":imgdata["ref_sessiondata_session"]})
    path = readInputPath(sessiondata['frame_path'],imgdata['filename'])
    return True if path else False