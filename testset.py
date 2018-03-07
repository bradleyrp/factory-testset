#!/usr/bin/env python

"""
TESTSETS FOR FACTORY
by Ryan Bradley
on 2017.10.23
"""

from config import read_config

__all__ = ['interpreter']

def interpreter(**kwargs):
  """
  Interpret this file for the importing function.
  We indent with spaces because there is a lot of YAML in this file.
  """
  import os,re
  collect = {}
  #---do something with incoming modifiers
  if 'mods' in kwargs and kwargs['mods']!=None:
    #---incoming modifiers can act on text 
    mod_fn = kwargs.pop('mods')
    if not os.path.isfile(mod_fn): raise Exception('cannot find modifier file %s'%mod_fn)
    with open(mod_fn) as fp: text = fp.read()
    exec(text,collect)
  #---collect modifiers
  text_changer = collect.pop('text_changer',lambda x:x)
  testset_processor = kwargs.pop('testset_processor',lambda x:x)
  if kwargs and any([i!=None for i in kwargs.values()]): print('[WARNING] unprocessed kwargs %s'%kwargs)
  #---interpret the testsets
  try: import yaml
  except: raise Exception('testset needs yaml. install with `pip install --user pyyaml`')
  global testsets
  #---make substitutions
  #---! are subs redundant with the changer and the modifier?
  testsets_subbed = str(testsets)
  global subs
  if subs!=None:
  	for key,val in subs.items(): 
  		testsets_subbed = re.sub(key,val,testsets_subbed)
  #---interpret the YAML directions with the processor and the changer
  text_changed = text_changer(testsets_subbed)
  text_proc = testset_processor(text_changed)
  tests = yaml.load(text_proc)
  counts = dict([(key,sum([set(i)==set(key) for i in tests])) for key in tests])
  if any([v!=1 for v in counts.values()]):
    raise Exception('duplicate key sets: %s'%counts)
  #---the dockerfile key points to variables in this script
  for key,val in tests.items():
    if 'script' in val:
      key_this = val['script']
      #---you can define the script directly in the test or point to a global variable
      if key_this in globals(): val['script'] = text_changer(globals()[key_this])
  return tests

# get the root docker location from the config (set with `make set DOCKER_SPOT="<path>"`)
# note also that you can use `@read_config('<key>')` in the YAML to look up keys from the config
docker_spot = read_config('config.py')['DOCKER_SPOT']
# global subsitutions in the text before YAML parsing
subs = {'DOCKER_SPOT':docker_spot}

###
### GENERAL TEST SETS
###

testsets_general = """

factory setup:
  notes: |
    This test will create a blank factory for other tests.
    Uses custom requirements files suitable for the barebones docker image from docker.py.
    This test should only be run once, while connection tests can be rerun until the connection is right.
    After you have a factory and a connection you can run the compute tests.
  # which docker to use
  docker: small-p2
  # prevent a rerun
  once: True
  # external location for running the factory
  where: DOCKER_SPOT
  # prepare to run the container
  preliminary: |
    mkdir DOCKER_SPOT/holding
    cp @read_config('location_miniconda') DOCKER_SPOT/holding/miniconda_installer.sh
  # copy local files
  collect files:
    reqs_conda_factory_setup_minimal.yaml: holding/reqs_conda_minimal.yaml
    reqs_pip_factory_setup.txt: holding/reqs_pip.txt
  # setup script
  script: |
    cd host
    git clone http://github.com/biophyscode/factory factory
    cd factory
    make nuke sure
    make set species anaconda
    make set anaconda_location=~/host/holding/miniconda_installer.sh
    make set automacs="http://github.com/biophyscode/automacs"
    make set omnicalc="http://github.com/biophyscode/omnicalc"
    cp ~/host/holding/reqs_conda_minimal.yaml .
    cp ~/host/holding/reqs_pip.txt .
    make set reqs_conda reqs_conda_minimal.yaml
    make set reqs_pip reqs_pip.txt
    make setup

factory refresh:
  notes: |
    Implement changes to anaconda requirements.
  # which docker to use
  docker: small-p2
  # external location for running the factory
  where: DOCKER_SPOT
  # prepare to run the container
  preliminary: |
    mkdir DOCKER_SPOT/holding
    cp @read_config('location_miniconda') DOCKER_SPOT/holding/miniconda_installer.sh
  # copy local files
  collect files:
    reqs_conda_factory_setup_minimal.yaml: holding/reqs_conda_minimal.yaml
    reqs_pip_factory_setup.txt: holding/reqs_pip.txt
  # setup script
  script: |
    cd host/factory
    cp ~/host/holding/reqs_conda_minimal.yaml .
    cp ~/host/holding/reqs_pip.txt .
    make setup
    rm -rf ~/host/holding

"""

###
### DEMONSTRATIONS
###

testsets_demos = """

demo serve:
  notes: |
    Serve the project in a detached mode with connected ports.
    Kill the container by name with `docker kill <name>` when finished.
    Note that you can remove the `public` flags and use ssh tunnels to test in dev mode.
    You can even develop from docker by setting the ports correctly and removing `public` flags.
    However there are problems with the interactive notebook over ssh for some reason.
  docker: docker_demo
  where: DOCKER_SPOT
  collect files: 
    automacs.py: .automacs.py
    connect_demo.yaml: factory/connections/connect_demo.yaml
    specs_demo_meta.yaml: specs_demo_meta.yaml
  script: | 
    { # log to holding
    cd host/factory
    make set automacs_branch dev
    make prepare_server
    DO_PUBLIC=public
    make connect demo $DO_PUBLIC
    mv ~/host/.automacs.py ~/.automacs.py
    mv ~/host/specs_demo_meta.yaml ~/host/factory/calc/demo/calcs/specs/specs_demo_dev.yaml
    source /usr/local/gromacs/bin/GMXRC.bash
    make run demo $DO_PUBLIC
    make unset automacs_branch
    cd ~/host/factory/calc/demo/
    source ../../env/bin/activate py2 
    make unset meta_filter
    make set meta_filter specs_demo_dev.yaml meta.current.yaml
    git clone http://github.com/bradleyrp/amx-martini ~/host/factory/calc/demo/amx-martini || \
    echo "[STATUS] amx-martini exists"
    } > ~/host/holding/log-watch 2>&1
    sleep infinity
  ports: [8008,8009]
  background: True
  write files:
    specs_demo_meta.yaml: | 
      plots:
        video_maker:
          script: video_maker.py
          autoplot: True
          collections: all
          calculation: protein_rmsd
          specs: {'scene':'video_scene_protein.py'}
    connect_demo.yaml: |
      # FACTORY PROJECT (the base case example "demo")
      demo:
        # include this project when reconnecting everything
        enable: true 
        site: site/PROJECT_NAME  
        calc: calc/PROJECT_NAME
        calc_meta_filters: ['specs_demo_meta.yaml','meta.current.yaml']
        repo: http://github.com/biophyscode/omni-basic
        database: data/PROJECT_NAME/db.factory.sqlite3
        post_spot: data/PROJECT_NAME/post
        plot_spot: data/PROJECT_NAME/plot
        simulation_spot: data/PROJECT_NAME/sims
        port: 8008
        notebook_port: 8009
        public:
          port: 8008
          notebook_port: 8009
          # use "notebook_hostname" if you have a router or zeroes if using docker
          notebook_hostname: '0.0.0.0'
          # you must replace the IP address below with yours
          hostname: [@read_config('HOST_IP'),'127.0.0.1']
          credentials: {'detailed':'balance'}
        # import previous data or point omnicalc to new simulations, each of which is called a "spot"
        # note that prepared slices from other integrators e.g. NAMD are imported via post with no naming rules
        spots:
          # colloquial name for the default "spot" for new simulations given as simulation_spot above
          sims:
            # name downstream postprocessing data according to the spot name (above) and simulation folder (top)
            # the default namer uses only the name (you must generate unique names if importing from many spots)
            namer: "lambda name,spot=None: name"
            # parent location of the spot_directory (may be changed if you mount the data elsewhere)
            route_to_data: data/PROJECT_NAME
            # path of the parent directory for the simulation data
            spot_directory: sims
            # rules for parsing the data in the spot directories
            regexes:
              # each simulation folder in the spot directory must match the top regex
              top: '(.+)'
              # each simulation folder must have trajectories in subfolders that match the step regex (can be null)
              # note: you must enforce directory structure here with not-slash
              step: '([stuv])([0-9]+)-([^\/]+)'
              # each part regex is parsed by omnicalc
              part: 
                xtc: 'md\.part([0-9]{4})\.xtc'
                trr: 'md\.part([0-9]{4})\.trr'
                edr: 'md\.part([0-9]{4})\.edr'
                tpr: 'md\.part([0-9]{4})\.tpr'
                # specify a naming convention for structures to complement the trajectories
                structure: '(system|system-input|structure)\.(gro|pdb)'

factory shell:
  where: DOCKER_SPOT
  docker: docker_demo
  ports: [8010]
  script: /usr/local/gotty/gotty -c detailed:balance -w -p 8010 bash
  background: True

demo protein generate:
  notes: |
    Generate source data for a validation of the code which reproduces a calculation.
    Requires the factory and a docker with GROMACS.
  docker: small-p4
  where: DOCKER_SPOT
  collect files: 
    automacs.py: ".automacs.py"
  script: |
    set -e
    cd host
    source /usr/local/gromacs/bin/GMXRC.bash
    #! this code needs retested without the factory since it should not depend on it
    source factory/env/bin/activate py2
    mv ~/host/.automacs.py ~/
    mkdir demo_protein_auto_data
    cd demo_protein_auto_data
    git clone http://github.com/biophyscode/automacs villin-rp1
    cd villin-rp1
    make setup proteins
    make go protein clean
    ln -s s01-protein production
    cd s01-protein
    #! unclear how to use timeout below with "set -e" above
    timeout --signal INT 300s ./script-continue.sh || exit 0

demo protein:
  notes: |
    Test the biophyscode.github.io use-case in which we analyze existing data.
    Requires `demo protein generate` above, and the factory.
    Note that we used the omni-basic repo at http://github.com/biophyscode/omni-basic at commit `31b903b`.
    This test set was added to the validation list.
  docker: docker_demo
  where: DOCKER_SPOT
  write files:
    connect_demo_protein.yaml: |
      proteins:
        site: site/PROJECT_NAME  
        calc: calc/PROJECT_NAME
        repo: https://github.com/biophyscode/omni-basic
        database: data/PROJECT_NAME/db.factory.sqlite3
        simulation_spot: data/PROJECT_NAME/sims
        # place to store post-processing data
        post_spot: data/PROJECT_NAME/post
        # place to store the resulting plots
        plot_spot: data/PROJECT_NAME/plot
        # public block is added to the testset for debugging
        public:
          port: 8010
          notebook_port: 8011
          # use "notebook_hostname" if you have a router or zeroes if using docker
          notebook_hostname: '0.0.0.0'
          hostname: [@read_config('HOST_IP'),'127.0.0.1']
          credentials: {'detailed':'balance'}
        spots:
          sims: 
            namer: "lambda name,spot=None: name"
            route_to_data: /home/rpb/host/
            spot_directory: demo_protein_auto_data
            regexes: # use regular expressions
              top: '(.+)' # regex to match simulation names
              step: '(production)' # all trajectories are in a subfolder
              part:
                xtc: 'md\.part([0-9]{4})\.xtc'
                trr: 'md\.part([0-9]{4})\.trr'
                edr: 'md\.part([0-9]{4})\.edr'
                tpr: 'md\.part([0-9]{4})\.tpr'
                structure: '(system|system-input|structure)\.(gro|pdb)'
    specs_demo_protein_meta.yaml: | 
      collections:
        one: [villin-rp1,]
      slices:
        villin-rp1:
          groups: {'protein_selection':'protein'}
          slices:
            short: 
              {'start':0,'end':400,'skip':4,
                'pbc':'mol','groups':['protein_selection']}
            long: 
              {'start':10000,'end':110000,'skip':200,
                'pbc':'mol','groups':['protein_selection']}
      calculations:
        protein_rmsd:
          slice_name: short
          group: protein_selection
          collections: one
      plots:
        video_maker:
          script: video_maker.py
          autoplot: True
          collections: one
          calculation: protein_rmsd
          specs: {'scene':'video_scene_protein.py'}
  collect files:
    connect_demo_protein.yaml: factory/connections/connect_demo_protein.yaml
    specs_demo_protein_meta.yaml: specs_demo_protein_meta.yaml
    automacs.py: ".automacs.py"
  script: |
    set -e
    cd host/factory
    mv ~/host/.automacs.py ~/.automacs.py
    source /usr/local/gromacs/bin/GMXRC.bash
    make prepare_server
    make connect proteins public
    #! remove public? no need to run?
    cd ~/host/factory/calc/proteins/
    git fetch origin dev
    git checkout dev
    source ../../env/bin/activate py2 
    mv ~/host/specs_demo_protein_meta.yaml calcs/specs/meta.yaml
    make unset meta_filter
    make set meta_filter meta.yaml
    make set mpl_agg=True
    make clear_stale || echo "no stale jobs"
    make compute
    echo "import sys;sys.exit(0)" | make plot protein_rmsd
    make plot video_maker make_videos

"""

#---concatenate the testsets
testsets = testsets_general + testsets_demos
