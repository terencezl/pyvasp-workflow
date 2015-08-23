pyvasp-workflow
===============

A simple yet flexible programmatic workflow of describing, submitting and analyzing VASP jobs.

**The main purposes of this repo are**

1. demonstrating an elegant and intuitive way of doing the messy work with VASP. The advantages build up especially when things get more complicated.
2. providing a few widely demanded routine examples to start with.

Please make sure you have installed [pymatgen](http://pymatgen.org/), and download or clone this repo:

    git clone https://github.com/terencezl/pyvasp-workflow

and rename it to whatever you wish to call your project. You'll start it within this directory.

**Note, this is not a Python package, so no need to install it.**

Files
-----

In the directory root, you'll see a directory called `INPUT/`, which contains a bunch of files to start with. They are:

1. a routine description file, ending with `.py`
2. a setting file, ending with `.yaml`, which will be parsed by the routine `.py` file
3. a deploy trigger file, typically ending with `.sh`, which submits a job script
4. a job script, according to your supercomputer cluster's setup. Here it's named `deploy.job`

To avoid cluttering of irrelevant files, under `INPUT/` there is only one set of `.py` and `.yaml` files. You'll need more as you define you own routines. For some examples, go to `STASH/`. For more (not-so-well-tested-and-documented) examples, go to `STASH/MORE`.

How to Run
----------

I assume your supercomputer cluster is using a queueing system to manage multi-users, which is the common practice in the field. If not, the job script is not needed, and the deploy trigger file needs to be adjusted.

0. Edit the files in `INPUT/` as below.
1. `run_module.py` has a few functions shared by other Python routine description files. Take a look around and find out what you can use. See the two lines:

   ```python
   VASP_EXEC = os.getenv('VASP_EXEC', 'OR-PATH-TO-YOUR-VASP-EXEC-default')
   VASP_POTENTIALS_DIR = os.getenv('VASP_POTENTIALS_DIR', 'OR-PATH-TO-YOUR-VASP_POTENTIALS_DIR-default')
   ```

   Point variables `VASP_EXEC` and `VASP_POTENTIALS_DIR` to your machine's configuration. You can either directly change the `'OR-PATH-TO-YOUR-*-default'` in `run_module.py`, or add the following lines to your `.bashrc` so that `run_module.py` can automatically finds them.

   ```bash
   export VASP_EXEC='PATH-TO-YOUR-VASP-EXEC'
   export VASP_POTENTIALS_DIR='PATH-TO-YOUR-VASP_POTENTIALS_DIR'
   ```

  * `VASP_EXEC` is the vasp executing command you would use in a shell. If mpi is used, don't forget to put it like `'mpirun vasp'`.
  * `VASP_POTENTIALS_DIR` is a directory that have sub-directories such as `PAW_LDA`, `PAW_PBE`, which contain proprietory potential files like `H/POTCAR`, `Na_sv/POTCAR`. The `POTCAR` files should not be in the zipped form (like in older distributions of VASP potentials).

2. Write up/alter the `.py` routine description file, to set up the basic flow of a set of runs you wish to conduct in a single job submission (one record in the supercomputer queueing system, having a given walltime).
3. Write up/alter the `.yaml` setting file, and provide the necessary information about this run, including `INCAR` tags, `KPOINTS` parameters, `POTCAR` types, involved elements, structure name, `POSCAR` parameters, etc. How you provide them highly depends on how you write your `.py` routine file. You can even omit the `.yaml` file and hardcode parameters into the `.py` routine file, but that would not give you a nice separation of layers.
4. Alter the `.sh` deploy trigger file and `deploy.job` script. Note that these two are supercomputer queueing system dependent, and you have to be familiar with it, and do some replacements with the command line tool `sed`. As an example, look at the included `deploy.sh` and `deploy.job`, meant but not limited for the [PBS](https://en.wikipedia.org/wiki/Portable_Batch_System) queueing system. 

   In particular, you should create a script called `M`, make it executable (`chmod +x M`) and add it in your `$PATH`, so that `deploy.sh` can use it to change the job name, stdout and errout file directory, etc. and then submit it by the line `M "$job"`.
   
   For PBS, the M file is simple.
   
   ```bash
   #!/usr/bin/env bash
   qsub $@
   ```

5. Go back one directory to the directory root, looking at `INPUT/`, and type in `INPUT/deploy.sh run_test`. If you create a `.yaml` file called `run_test_2.yaml`, do `INPUT/deploy.sh run_test run_test_2.yaml` to select your alternative setting file.
