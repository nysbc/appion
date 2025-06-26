import dask_jobqueue
from dask.distributed import LocalCluster

# This is a separate helper function that creates a Dask cluster object.
# The cluster initialization/instantiation occurs here because this simplifies switching between
# local and SLURM-based clusters for testing.
def constructCluster(clusterconfig : dict):
    '''
    Initializes a Dask cluster object.  clusterconfig is a dict that specifies the cluster type, the kwargs to pass to the Dask constructor, and settings for any
    misc methods that need to be run for the cluster (e.g., adapt for autoscaling)
    '''
    cluster=None
    if clusterconfig["cluster_type"] in ["HTCondorCluster", "LSFCluster", "MoabCluster", "OARCluster", "PBSCluster", "SGECluster", "SLURMCluster"]:
        exec("cluster = dask_jobqueue.%s(**clusterconfig[\"kwargs\"])" % clusterconfig["cluster_type"])
        if "methods" in clusterconfig.keys():
            if "adapt" in clusterconfig["methods"].keys():
                cluster.adapt(**clusterconfig["methods"]["adapt"])
            if "scale" in clusterconfig["methods"].keys():
                cluster.scale(**clusterconfig["methods"]["scale"])
    elif clusterconfig["cluster_type"] == "LocalCluster":
        cluster = LocalCluster()
    return cluster