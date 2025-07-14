import os
from dask_jobqueue import SLURMCluster
from dask.distributed import LocalCluster

# This is a separate helper function that creates a Dask cluster object.
# The cluster initialization/instantiation occurs here because this simplifies switching between
# local and SLURM-based clusters for testing.
def constructCluster(clusterconfig : dict, rundir : str):
    '''
    Initializes a Dask cluster object.  clusterconfig is a dict that specifies the cluster type, the kwargs to pass to the Dask constructor, and settings for any
    misc methods that need to be run for the cluster (e.g., adapt for autoscaling)
    '''
    cluster=None
    if clusterconfig["cluster_type"] == "SLURMCluster":
        # Place log, spillover, and temp directories into the individual session's run directory.
        log_directory = os.path.join(rundir, "logs")
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        clusterconfig["kwargs"]["log_directory"] = log_directory  

        local_directory = os.path.join(rundir, "spillover")
        if not os.path.exists(local_directory):
            os.makedirs(local_directory)    
        clusterconfig["kwargs"]["local_directory"] = local_directory   

        shared_temp_directory = os.path.join(rundir,"temp")
        if not os.path.exists(shared_temp_directory):
            os.makedirs(shared_temp_directory)  
        clusterconfig["kwargs"]["shared_temp_directory"] = shared_temp_directory  

        cluster = SLURMCluster(**clusterconfig["kwargs"])
        #if "adapt" in clusterconfig.keys():
        #    cluster.adapt(**clusterconfig["adapt"])
    elif clusterconfig["cluster_type"] == "LocalCluster":
        cluster = LocalCluster()
    else:
        raise RuntimeError("Unsupported cluster type: %s" % clusterconfig["cluster_type"])
    return cluster