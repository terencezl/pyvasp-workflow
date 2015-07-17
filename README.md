pyvasp-workflow
===============

A simple yet flexible programmatic workflow of describing, submitting and analyzing VASP jobs.

**The main purpose of this repo is**

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

To avoid cluttering of irrelevant files, under `INPUT/` there is only one set of `.py` and `.yaml` files. You'll need more as you define you own routines. For some examples, go to `STASH/`. For more (not-so-well-tested-and-documented) examples, go to `STASH/less-used`.

How To Run
----------

I assume your supercomputer cluster is using a queueing system to manage multi-users, which is the common practice in the field. If not, the job script is not needed, and the deploy trigger file needs to be adjusted.

0. Edit the files in `INPUT/` as below.
1. `run_module.py` has a few functions shared by other python routine description files. Take a look around. Point variables `POTENTIAL_DATABASE` and `VASP` in the beginning to your machine's configuration.

  * `POTENTIAL_DATABASE` is a directory that have sub-directories like `PAW_LDA`, `PAW_PBE`, which contain proprietory potential files like `H/POTCAR`, `Na_sv/POTCAR`. The `POTCAR` files should not be in the zipped form (like in older distributions of VASP).
  * `VASP` is the vasp executing command you would use in a shell. If mpi is used, don't forget to put it like `'mpirun vasp'`.

2. Write up/alter the `.py` routine description file, to set up the basic flow of a set of runs you wish to conduct in a single job submission (one record in the supercomputer queueing system, having a given walltime).
3. Write up/alter the `.yaml` setting file, and provide the necessary information about this run, including `INCAR` tags, `KPOINTS` parameters, `POTCAR` types, involved elements, structure name, `POSCAR` parameters, etc. How you provide them highly depends on how you write your `.py` routine file. You can even omit the `.yaml` file and hardcode parameters into the `.py` routine file, but that would not give you a nice separation of layers.
4. Alter the `.sh` deploy trigger file and `deploy.job` script. Note that these two are supercomputing queueing system dependent, and you have to be familiar with it, and do some replacements in `.sh` with the command line tool `sed`.
5. Go back one directory to the directory root, looking at `INPUT/`, and type in `bash INPUT/deploy.sh run_test`.
