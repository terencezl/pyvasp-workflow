pyvasp-workflow
===============

A simple yet flexible programmatic workflow of describing, submitting and analyzing VASP jobs.

**The main purposes of this repo are**

1. demonstrating an elegant (I think) and intuitive way of doing the messy work with VASP. The advantages build up especially when things get more complicated and conditional.
2. providing a few widely demanded routine examples to start with.

Please make sure you have installed [pymatgen](http://pymatgen.org/), and download or clone this repo:

    git clone https://github.com/terencezl/pyvasp-workflow

and rename it to whatever you wish to call your project. You'll start it within this directory.

**Note, this is not a Python package, so no need to install it.**

Files
-----

In the directory root, you'll see a directory called `INPUT/`, which contains a bunch of files to start with. They are:

1. a routine description file, ending with `.py`
2. a specs file, ending with `.yaml`, which will be parsed by the routine `.py` file
3. a job script, according to your supercomputer's setup. Here it's named `deploy.job`
4. a deploy trigger file `deploy.py`, which submits the job script of the routine to the queue

To avoid cluttering of irrelevant files, under `INPUT/` there is only one set of `.py` and `.yaml` files. You'll need more as you define you own routines. For a bunch of examples, go to `STASH/`.

How to Run
----------

I assume your supercomputer is using a queueing system to manage multi-users, which is the common practice in the field. If not, it's even easier.

1. `run_module.py` has a few functions shared by other Python routine description files. Take a look around and find out what you can use. See the two lines:

   ```python
   VASP_EXEC = os.getenv('VASP_EXEC', 'OR-PATH-TO-YOUR-VASP-EXEC-default')
   VASP_POTENTIALS_DIR = os.getenv('VASP_POTENTIALS_DIR', 'OR-PATH-TO-YOUR-VASP_POTENTIALS_DIR-default')
   ```

   Point variables `VASP_EXEC` and `VASP_POTENTIALS_DIR` to your machine's configuration. You can either directly change the `'OR-PATH-TO-YOUR-*-default'` in `run_module.py`, or **preferrably add the following lines to your `.bashrc`** so that `run_module.py` can automatically find them as shell environmental variables.

   ```bash
   # edit ~/.bashrc yourself
   export VASP_EXEC='PATH-TO-YOUR-VASP-EXEC'
   export VASP_POTENTIALS_DIR='PATH-TO-YOUR-VASP_POTENTIALS_DIR'
   ```

  * `VASP_EXEC` is the vasp executing command you would use in a shell. If mpi is used, don't forget to put it like `'mpirun vasp'`.
  * `VASP_POTENTIALS_DIR` is a directory that has sub-directories such as `PAW_LDA`, `PAW_PBE`, which contain potential files like `H/POTCAR`, `Na_sv/POTCAR`. The `POTCAR` files should not be in the zipped form (like in older distributions of VASP potentials).

2. Write up/alter the `.py` routine description file, to set up the basic flow of a set of runs you wish to conduct in a single job submission (one record in the supercomputer queueing system, having a given walltime).

3. Write up/alter the `.yaml` specs file, and provide the necessary information about this run, including `INCAR` tags, `KPOINTS` parameters, `POTCAR` type and element types, `POSCAR` parameters, etc. How you provide them highly depends on how you write your `.py` routine file. See a few examples included to get started. *You can even omit the `.yaml` file and hardcode parameters into the `.py` routine file, but that would not give you a nice separation of layers.*

4. Alter the `deploy.job` script. Note that this is supercomputer queueing system dependent. As an example, look at the included `deploy.job`, meant but not limited for the [PBS](https://en.wikipedia.org/wiki/Portable_Batch_System) queueing system.

  You have to be familiar with its syntax, and able to do some replacements with the command line tool `sed`. **In particular, you should create a script called `M`, make it executable and add it in your `$PATH`. **This way, the deploy trigger file `deploy.py` can use it to change the job name, stdout and stderr file path, etc., and then submit it (see `deploy.py` if interested).
   
   As an example, for PBS, the `M` file is simple. Use it with the included `deploy.job` file.
   
   ```bash
   # create a directory to store the executable and enter it
   mkdir -p ~/local/bin
   cd ~/local/bin

   # write the executable script M
   cat > M <<!
   #!/usr/bin/env bash
   qsub "$@"
   !

   # make file executable
   chmod +x M

   # edit ~/.bashrc yourself, or append to it
   echo 'export PATH="$PATH:~/local/bin"' >> ~/.bashrc
   ```

5. Go back one directory to the directory root, looking at `INPUT/`, and type in

   ```bash
   INPUT/deploy.py INPUT/run_test
   # if you create INPUT/run_test_2.yaml
   INPUT/deploy.py INPUT/run_test INPUT/run_test_2.yaml
   ```

**Now, if your supercomputer doesn't have a queueing system, or you are already in an interactive session, skip 4 and 5, just**

```bash
python INPUT/run_test.py
# or for the specs file INPUT/run_test_2.yaml
python INPUT/run_test.py INPUT/run_test_2.yaml
```

Priority Rules
--------------

There are a few priority rules implemented for most example routines regarding which value for a certain parameter to take, if there are more than one to choose from. This gives flexibility to the scripts by simply omitting setting some tags in th specs file. However, whatever you provide in the specs will be given precedence to.

* For INCAR, if 'ISPIN' is not provided in the specs file under 'incar', a ../properties.json file is attempted and if it exists, it should contain a 'mag' field with the cell's magnetic moment. ISPIN value is set to 2 if mag is larger than 0.001.

* For POSCAR, if 'poscar' is not provided in the specs file, a ../POSCAR is attempted.

Dependencies
------------

* NumPy
* SciPy
* matplotlib
* pydass_vasp (https://github.com/terencezl/pydass_vasp) (needed by some scripts)
