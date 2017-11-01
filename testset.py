#!/usr/bin/env python

"""
TESTSETS FOR FACTORY
by Ryan Bradley
on 2017.10.23
"""

__all__ = ['interpreter']

def interpreter(**kwargs):
  """
  Interpret this file for the importing function.
  We indent with spaces because there is a lot of YAML in this file.
  """
  import os
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
  import yaml
  global testsets
  text_changed = text_changer(testsets)
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

testsets = """

### GENERIC

factory setup:
  notes: |
    This test will create a blank factory for other tests.
    Uses custom requirements files suitable for the "basic" docker image from config_docker.py.
    This test should only be run once, while connection tests can be rerun until the connection is right.
    After you have a factory and a connection you can run the compute tests.
  # which docker to use
  docker: basic
  # prevent a rerun
  once: True
  # external location for running the factory
  where: ~/omicron/PIER/
  # prepare to run the container
  preliminary: |
    #!/bin/bash
    mkdir ~/omicron/PIER/holding
    cp @read_config('location_miniconda') ~/omicron/PIER/holding/miniconda_installer.sh
  # copy local files
  #! very annoying to do this at the top level!
  collect files:
    reqs_conda_factory_setup.yaml: holding/reqs_conda.yaml
    reqs_pip_factory_setup.txt: holding/reqs_pip.txt
  # setup script
  script: |
    git clone http://github.com/biophyscode/factory factory
    cd factory
    make nuke sure
    make set species anaconda
    make set anaconda_location=~/holding/miniconda_installer.sh
    make set automacs="http://github.com/biophyscode/automacs"
    make set omnicalc="http://github.com/biophyscode/omnicalc"
    cp ~/holding/reqs_conda.yaml .
    cp ~/holding/reqs_pip.txt .
    make set reqs_conda reqs_conda.yaml
    make set reqs_pip reqs_pip.txt
    make setup
    make prepare_server
    rm -rf ~/holding

factory visit:
  where: ~/omicron/PIER/
  docker: basic
  visit: True

### PTDINS PROJECT

ptdins connect:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-project-ptdins: analyze-project-ptdins
    ~/omicron/dataset-project-ptdins: dataset-project-ptdins
  collect files: 
    connect_ptdins.yaml: factory/connections/connect_ptdins.yaml
  script: cd factory && make connect ptdins

ptdins serve:
  notes: |
    Serve the project in a detached mode with connected ports.
    Kill the container by name with "docker kill --signal=9" name when finished.
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-project-ptdins: analyze-project-ptdins
    ~/omicron/dataset-project-ptdins: dataset-project-ptdins
  script: cd factory && make connect ptdins public && make run ptdins public && sleep infinity
  ports: [8006,8007]
  background: True

ptdins compute:
  notes: |
    Run compute on the PtdIns project.
    Run via: "make config=custom_docker_testsets/docker_config.py test ptdins compute"
  docker: basic
  container_site: /root
  where: ~/omicron/PIER
  collect files:
    specs_ptdins_v1.yaml: specs_ptdins_v1.yaml
  mounts:
    ~/omicron/analyze-project-ptdins: analyze-project-ptdins
    ~/omicron/dataset-project-ptdins: dataset-project-ptdins
  script: |
    cd factory/calc/ptdins
    cp ~/specs_ptdins_v*.yaml calcs/specs/
    make compute meta=calcs/specs/specs_ptdins_v1.yaml

### OCEAN PROJECT

ocean connect:
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    connect_ocean.yaml: factory/connections/connect_ocean.yaml
  report files: ['connect_ocean.yaml']
  mounts:
    ~/omicron/analyze-project-ocean/post: analyze-project-ocean-post
    ~/omicron/analyze-project-ocean/plot: analyze-project-ocean-plot
  script: cd ~/factory && make connect ocean

ocean compute:
  docker: basic
  where: ~/omicron/PIER
  collect files:
    specs_ocean_v1.yaml: factory/calc/ocean/calcs/specs/specs_ocean_v1.yaml
    specs_ocean_v2.yaml: factory/calc/ocean/calcs/specs/specs_ocean_v2.yaml
    specs_ocean.yaml: factory/calc/ocean/calcs/specs/specs_ocean.yaml
  mounts:
    ~/omicron/analyze-project-ocean/post: analyze-project-ocean-post
    ~/omicron/analyze-project-ocean/plot: analyze-project-ocean-plot
  script: |
    cd factory/calc/ocean
    make compute meta=calcs/specs/specs_ocean_v1.yaml
    make compute meta=calcs/specs/specs_ocean_v2.yaml
    make compute meta=calcs/specs/specs_ocean.yaml

ocean plots:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-project-ocean/post: analyze-project-ocean-post
    ~/omicron/analyze-project-ocean/plot: analyze-project-ocean-plot
  collect files:
    specs_ocean.yaml: factory/calc/ocean/calcs/specs/specs_ocean.yaml
    specs_ocean_plot_lipid_mesh.yaml: factory/calc/ocean/calcs/specs/specs_ocean_plot_lipid_mesh.yaml
  script: |
    cd factory/calc/ocean
    make set mpl_agg=True
    make unset meta_filter && make set meta_filter specs_ocean.yaml
    make plot undulations plot_height_profiles
    make plot undulations undulation_spectra
    make unset meta_filter && make set meta_filter specs_ocean.yaml specs_ocean_plot_lipid_mesh.yaml
    make set merge_method sequential
    make plot lipid_mesh plot_curvature_maps
    make unset merge_method

ocean coupling:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-project-ocean/post: analyze-project-ocean-post
    ~/omicron/analyze-project-ocean/plot: analyze-project-ocean-plot
  collect files:
    specs_ocean.yaml: factory/calc/ocean/calcs/specs/specs_ocean.yaml
    specs_ocean_curvature_undulation_coupling.yaml: 
      factory/calc/ocean/calcs/specs/specs_ocean_curvature_undulation_coupling.yaml
  script: |
    cd factory/calc/ocean
    make set mpl_agg=True
    make unset meta_filter
    make set merge_method sequential
    make set meta_filter specs_ocean.yaml specs_ocean_curvature_undulation_coupling.yaml
    make compute
    make plot curvature_undulation_coupling individual reviews
    make unset merge_method

### "Collar" demo

collar connect:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/dataset-project-collar: dataset-project-collar
    ~/omicron/analyze-demo-collar: analyze-demo-collar
  collect files:
    connect_collar_demo.yaml: factory/connections/connect_collar_demo.yaml
  script: cd factory && make connect collar_demo

collar compute:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-demo-collar/post: analyze-demo-collar-post
    ~/omicron/analyze-demo-collar/plot: analyze-demo-collar-plot
  collect files:
    specs_collar_demo.yaml: factory/calc/collar_demo/calcs/specs/collar_demo.yaml
    art_collar.py: factory/calc/collar_demo/calcs/art_collar.py
  script: cd factory/calc/collar_demo && make compute

collar plots:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-demo-collar/post: analyze-demo-collar-post
    ~/omicron/analyze-demo-collar/plot: analyze-demo-collar-plot
  collect files:
    specs_collar_demo.yaml: factory/calc/collar_demo/calcs/specs/collar_demo.yaml
    art_collar.py: factory/calc/collar_demo/calcs/art_collar.py
  script: |
    cd factory/calc/collar_demo
    make set mpl_agg=True
    make plot undulations plot_height_profiles
    make plot undulations undulation_spectra
    make plot lipid_mesh plot_curvature_maps

### BANANA PROJECT

banana connect:
  docker: basic
  where: ~/omicron/PIER
  report files: ['connect_banana.yaml']
  collect files: 
    connect_banana.yaml: factory/connections/connect_banana.yaml
  mounts:
    /store-sigma/yards/DATA/analyze-project-banana/post: analyze-project-banana-post
    /store-sigma/yards/DATA/analyze-project-banana/plot: analyze-project-banana-plot
    /store-sigma/yards/DATA/dataset-project-banana: dataset-project-banana
  script: cd ~/factory && make connect banana

banana times:
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    connect_banana.yaml: factory/connections/connect_banana.yaml
    automacs.py: ".automacs.py"
  mounts:
    /store-sigma/yards/DATA/analyze-project-banana/post: analyze-project-banana-post
    /store-sigma/yards/DATA/analyze-project-banana/plot: analyze-project-banana-plot
    /store-sigma/yards/DATA/dataset-project-banana: dataset-project-banana
  script: |
    cd ~/factory/calc/banana
    source /usr/local/gromacs/bin/GMXRC.bash
    make look times

banana compute:
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    automacs.py: ".automacs.py"
    specs_banana.yaml: factory/calc/banana/calcs/specs/specs_banana.yaml
  mounts:
    /store-sigma/yards/DATA/analyze-project-banana/post: analyze-project-banana-post
    /store-sigma/yards/DATA/analyze-project-banana/plot: analyze-project-banana-plot
    /store-sigma/yards/DATA/dataset-project-banana: dataset-project-banana
  script: |
    cd ~/factory/calc/banana
    source /usr/local/gromacs/bin/GMXRC.bash
    make unset meta_filter && make set meta_filter specs_banana.yaml
    make compute

banana plots:
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    automacs.py: ".automacs.py"
    specs_banana.yaml: factory/calc/banana/calcs/specs/specs_banana.yaml
  mounts:
    /store-sigma/yards/DATA/analyze-project-banana/post: analyze-project-banana-post
    /store-sigma/yards/DATA/analyze-project-banana/plot: analyze-project-banana-plot
    /store-sigma/yards/DATA/dataset-project-banana: dataset-project-banana
  script: |
    cd ~/factory/calc/banana
    source /usr/local/gromacs/bin/GMXRC.bash
    make unset meta_filter && make set meta_filter specs_banana.yaml
    make set mpl_agg=True
    make plot undulations plot_height_profiles
    make plot undulations undulation_spectra
    make plot lipid_mesh plot_curvature_maps

### DEMONSTRATIONS

demo protein serve:
  notes: |
    Serve the project in a detached mode with connected ports.
    Kill the container by name with docker kill name when finished.
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    automacs.py: .automacs.py
    connect_demo_protein.yaml: factory/connections/connect_demo_protein.yaml
    specs_demo_protein.yaml: factory/calc/demo_protein/calcs/specs/specs_demo_protein.yaml
  script: |
    cd factory
    source /usr/local/gromacs/bin/GMXRC.bash
    make connect demo_protein public
    make run demo_protein public
    sleep infinity
  ports: [8004,8005]
  background: True

demo dev serve:
  notes: |
    Serve the project in a detached mode with connected ports.
    Kill the container by name with docker kill name when finished.
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    automacs.py: .automacs.py
    connect_demo_dev.yaml: factory/connections/connect_demo_dev.yaml
    specs_demo_dev.yaml: factory/calc/demo_dev/calcs/specs/specs_demo_dev.yaml
  script: |
    cd factory
    source /usr/local/gromacs/bin/GMXRC.bash
    make set automacs_branch dev
    make connect demo_dev public
    make run demo_dev public
    make unset automacs_branch
    sleep infinity
  ports: [8008,8009]
  background: True

"""
