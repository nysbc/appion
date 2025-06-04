# SEMC Appion 

## Background

SEMC Appion is a refactor of the Leginon Cryo-EM suite's Appion program (classic Appion).  It exists primarily because the original Appion was experiencing scaling issues due to a facilties expansion in January 2025 (more microscopes!) and because we started working with larger datasets (in [EER format](https://guide.cryosparc.com/processing-data/tutorials-and-case-studies/tutorial-eer-file-support)) more often than previously.  The goals of our refactor were as follows:

1. Reduce the burden of maintaining Appion by switching from in-house libraries (`sinedon`, `numextension`, Appion's pipelining/orchestration functionality) to mainstream external libraries (e.g., `django`, `numpy` with `numba`, and `dask`) with extensive community and institutional support.
2. Remove unused functionality / clean up the codebase so that only what is being actively used at SEMC is present.
3. Switch to a functional programming paradigm from object-oriented programming.  The underlying motivation with this goal was to increase codebase clarity and also make it easier to adapt the codebase to use services/tools that expect functions (e.g., AWS Lambda, `dask`).
4. Leverage [Dask futures](https://docs.dask.org/en/stable/futures.html) and [Dask Slurm jobqueue](https://jobqueue.dask.org/en/latest/generated/dask_jobqueue.SLURMCluster.html) to create autoscaling pools of workers that can elastically expand/contract depending on how many exposures are taken in a session.  These workers would run on top of Slurm.  Underlying this goal was a core concern that Appion never fall too far behind when processing EM images in near-realtime.  Building around `dask-jobqueue` would also give us the option of making it easier to migrate our code to other job schedulers / orchestrators with minimal effort. 
5. Create drop-in replacement entrypoints / command line interfaces for classic Appion.

## Architecture

Refactored Appion consists of several different stacks.

### Data Plane

1. Generic Data Storage / Retrieval: `mrcfile`, `glob`, `django`, `json`
2. Data Model: `sinedon`
3. Results and Parameters Storage / Retrieval: `savePathData`, etc

We concern ourselves with layers 2 and 3, with layer 2 exhibiting a slower rate of change than layer 3.  Our refactored version of Leginon's `sinedon` library (layer 2) can be found [here](https://github.com/nysbc/sinedon).

### Internal Calculations / Pure Functions

These are calculations that don't require running any external commands.

1. Data Structures: `numpy`, Python built-ins
2. Generic Mathematical Calculations: `math`, `scipy`
3. Application-Specific Calculations: `calcKV`, etc

We concern ourselves with layer 3.

### External Calculations / Impure Functions

These calculations involve running an external command via  `subprocess` or `pexpect` (or similar).

1. Execution Libraries: `pexpect`, `subprocess`
2. Specific Applications: `motioncor2`, `motioncor3`, `ctffind4`, `gctf`
3. Generic Wrappers: `calcMotionCorrection`, `calcCTF`

We concern ourselves with layer 3.

### Runtime

This is the stack that ties everything together.  At the uppermost layer is a daemon that loops until SIGTERM is received.  This daemon uses functions from the data plane to query for parameters, uses the calculation stacks to perform processing, and then stores the results using the data plane functions.  The runtime stack is used to run all of these functions with interchangeable backends.  The daemon also takes in user-provided parameters.

1. Cluster Orchestration : Local OS kernel, slurm, kubernetes, etc
2. Lightweight Orchestration: `dask`
3. Controller: `loop.py`

We concern ourselves with layers 2 and 3.

## Versioning Scheme

SEMC Appion's version string is of the form `YYYY.MM.DD`, which reflects the date of the release.  If there are multiple releases within the same day, the version string can be of the form `YYYY.MM.DD.HH`.  The following suffixes may also be appended to the version string: `a` or `b`.  These indicate alpha and beta releases respectively.  Alpha releases have not been tested at all, and the code is not guaranteed to even run.  Beta releases can run, but extensive testing for regressions / unexpected exceptions and logic issues has not occurred.

## Package Organization

`base` is a submodule that consists of common code that is shared by two or more processing steps.  Each other submodule (e.g., `ctfestimation`, `motioncorrection`, etc) contains code related to a specific processing step in the Cryo-EM reconstruction pipeline.  Currently only `ctfestimation` and `motioncorrection` are implemented, but particle picking (via `topaz`) and 2d/3d reconstruction submodules could also be added in the future if desired/needed.

Each submodule contains the following nested submodules:

* `calc` contains both pure and impure functions.  In some top-level submodules, `calc` is a single file.  For others, `calc` is further split up into functions that live in `internal` (pure functions and/or functions that don't call outside programs) and `external` (functions that call external commands like `motioncor2` and `ctffind4`).
* `cli` contains functions that are used by the main CLI wrapper command that initiates processing.
* `retrieve` contains functions that retrieve state from external data stores (e.g., database, filesystem)
* `store` contains functions that update external data stores (e.g., database, filesystem)

Generally, functions with side effects should go into `retrieve` or `store`.  `calc.internal` should consist primarily of pure functions, except when it makes sense to break this convention. `calc.external` should always be where wrappers around command line programs should go.