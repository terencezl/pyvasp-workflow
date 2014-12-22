VASP-routines-with-pymatgen
===========================

A programmatic workflow of defining, submitting and analyzing VASP run routines with pymatgen, very robust and flexible.

**The main purpose of this repo is suggesting a less cluttered, don't-repeat-yourself way of doing the messy work with VASP, especially when things get complicated.**

Please

    git clone https://github.com/terencezl/VASP-routines-with-pymatgen

and rename it to whatever you wish to call your project. You'll work within this directory for this project.

Introduction
------------

In the directory root, you'll see a folder called `INPUT/`, which contains a bunch of files to start with. They are:

1. routine definition python files, ending with `.py`,
2. setting files, ending with `.yaml`, which will be parsed by the routine `.py` files,
3. a job submission script (template), ending with `.job`,
4. (optional) a deploy trigger file, typically ending with `.sh`, which submits the `.job` script.

The workflow is like this:

1. Get into `INPUT/`.
2. Write up/alter the `.py` routine definition files, to set up the basic flow of a set of runs you wish to conduct in a single job submission (one record in the supercomputer queueing system, having a given walltime).
3. Write up/alter the `.yaml` file, and provide the necessary information about this run, including `INCAR` tags, `KPOINTS` parameters, `POTCAR` types, involved elements, structure name, `POSCAR` parameters, etc. How you provide them highly depends on how you write your `.py` routine files. You can even omit the `.yaml` file and hardcode parameters into the `.py` routine files, but that would not give you a nice separation of layers.
4. Write up/alter the `.job` file, according to the names you give to the `.py` files. This is supercomputing queueing system dependent.
5. If you want to do this routine for more than one composition, or a set of runs with some other parameters in the `.yaml` file changing, you'll need the `.sh` deploy trigger file. In it, code up a loop.
	1. Copy the `.yaml` setting file out one level from the `INPUT/` folder, with a file name denoting the changing parameter in the `.yaml` file (e.g. elements).
	2. Substitute the content of the `.yaml` setting file, that changing parameter.
	3. Substitute the `.job` submission file, taking the `.yaml` file name as an argument for the `python YOUR-PY-FILE` command.
	4. Submit the `.job` file.
6. Go back to the directory root, looking at `INPUT/`, and finally submit the `.job` file by, e.g. `qsub INPUT/run_volume.job`, or through your `.sh` trigger file by, e.g. `bash INPUT/deploy.sh`.

Test run
--------

If you would like to have a try of the already existing routines, note that `run_module.py` has a few commonly used routine functions, and remember to point variable `POTENTIAL_DATABASE` and `VASP` in the beginning to your machine's configuration.

* `POTENTIAL_DATABASE` should have directories like `PAW-LDA`, `PAW-PBE`, which contain proprietory potential files like `POTCAR_H`, `POTCAR_Na_sv`. Yes, they are not in the out-of-the-box zipped form, so please create the directory and sub-directories like them and unzip the individual `POTCAR.Z` files in the denoted format for your future conveniences. If you don't like to do this, the POTCAR part of `run_module.py` needs to be changed accordingly. Well you are supposed get yourself familiarized with python and pymatgen to write up your own routines anyway :D.
* `VASP` is the vasp executable, preferably MPI compiled.