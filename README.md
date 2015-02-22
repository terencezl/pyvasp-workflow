pyvasp-routines
===========================

A programmatic workflow of defining, submitting and analyzing VASP run routines with pymatgen, very robust and flexible.

**The main purpose of this repo is suggesting a less cluttered, don't-repeat-yourself way of doing the messy work with VASP, especially when things get complicated.**

Please

    git clone https://github.com/terencezl/pyvasp-routines

and rename it to whatever you wish to call your project. You'll work within this directory for this project.

Introduction
------------

In the directory root, you'll see a folder called `INPUT/`, which contains a bunch of files to start with. They are:

1. routine definition python files, ending with `.py`,
2. setting files, ending with `.yaml`, which will be parsed by the routine `.py` files,
3. deploy trigger files, typically ending with `.sh`, which submit the job.

The workflow is like this:

1. Get into `INPUT/`.
2. Write up/alter the `.py` routine definition files, to set up the basic flow of a set of runs you wish to conduct in a single job submission (one record in the supercomputer queueing system, having a given walltime).
3. Write up/alter the `.yaml` file, and provide the necessary information about this run, including `INCAR` tags, `KPOINTS` parameters, `POTCAR` types, involved elements, structure name, `POSCAR` parameters, etc. How you provide them highly depends on how you write your `.py` routine files. You can even omit the `.yaml` file and hardcode parameters into the `.py` routine files, but that would not give you a nice separation of layers.
4. Write up/alter the `deploy.job` file. This is to be used as a template submission script, and will be processed by the `.sh` deploy trigger files. Note that this is supercomputing queueing system dependent, and may not even be needed.
5. If you want to do this routine for more than one composition, or a set of runs with some other parameters in the `.yaml` file changing, you'll need the `.sh` deploy trigger files. In it, code up a loop and express the following.
	1. Substitute the content of the `.yaml` setting file, that changing parameter.
	2. If a `deploy.job` submission script is needed, substitute the submission script, taking the `.yaml` file name as an argument for the `python YOUR-PY-FILE` command.
	3. Run python with the line ending with a `&` to run in background. Or, submit the `.job` file.
6. Go back to the directory root, looking at `INPUT/`, and run the `.py` file or subimit the job. Alternatively, run/submit through your `.sh` trigger files by, e.g. `bash INPUT/deploy.sh`.

Test run
--------

If you would like to have a try of the already existing routines, note that `run_module.py` has a few commonly used routine functions, and remember to point variable `POTENTIAL_DATABASE` and `VASP` in the beginning to your machine's configuration.

* `POTENTIAL_DATABASE` should have directories like `PAW_PBE`, which contain proprietory potential files like `H/POTCAR`, `Na_sv/POTCAR`. They should not be in the out-of-the-box zipped form, so please unzip the individual `POTCAR.Z` files in their respective directories for your future conveniences. If you don't like to do this, the POTCAR part of `run_module.py` needs to be changed accordingly.
* `VASP` is the vasp executable, preferably MPI compiled.
