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
    After you have a factory and a connection you can run the compute tests below.
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
    rm -rf ~/holding

factory visit:
  where: ~/omicron/PIER/
  docker: basic
  visit: True

### PtdIns project

ptdins connect:
  notes: |
    Connect to the PtdIns dataset on dark. 
    Run once unless you change the connection file.
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-project-ptdins: analyze-project-ptdins
    ~/omicron/dataset-project-ptdins: dataset-project-ptdins
  collect files: 
    connect_ptdins.yaml: connect_ptdins.yaml
  script: |
    cp connect_ptdins.yaml factory/connections/
    cd factory
    make connect ptdins

ptdins compute:
  notes: |
    Run compute on the PtdIns project.
    Run via: "make config=custom_docker_testsets/docker_config.py test ptdins compute"
  docker: basic
  container_site: /root
  where: ~/omicron/PIER
  #! all files are collected in the root and then the script has to get them? should they be cleaned?
  collect files:
    specs_ptdins_v1.yaml: specs_ptdins_v1.yaml
  mounts:
    ~/omicron/analyze-project-ptdins: analyze-project-ptdins
    ~/omicron/dataset-project-ptdins: dataset-project-ptdins
  script: |
    cd factory/calc/ptdins
    cp ~/specs_ptdins_v*.yaml calcs/specs/
    make compute meta=calcs/specs/specs_ptdins_v1.yaml

### Ocean project

ocean connect:
  docker: basic
  where: ~/omicron/PIER
  collect files: 
    connect_ocean.yaml: connect_ocean.yaml
  mounts:
    ~/omicron/analyze-project-ocean/post: analyze-project-ptdins-outside-post
  collect requirements: |
    #!/bin/bash
    set -e
    cd ~/omicron/PIER/
    mkdir analyze-project-ocean-post
    cd analyze-project-ocean-post
    ln -s /home/rpb/analyze-project-ptdins-outside-post/BMEM_sample.dcd
    ln -s /home/rpb/analyze-project-ptdins-outside-post/1protein_again2_autopsf.psf
  script: |
    cp connect_ocean.yaml factory/connections/
    cd ~/factory
    make connect ocean

ocean compute:
  notes: |
    Compute series for the ocean project.
    This set is used to reproduce a bunch of bilayer calculations on a small atomistic bilayer.
  docker: basic
  where: ~/omicron/PIER
  collect files:
    specs_ocean_v1.yaml: specs_ocean_v1.yaml
    specs_ocean_v2.yaml: specs_ocean_v2.yaml
    specs_ocean_v3.yaml: specs_ocean_v3.yaml
  mounts:
    ~/omicron/analyze-project-ocean/post: analyze-project-ptdins-outside-post
  script: |
    cd factory/calc/ocean
    cp ~/specs_ocean_v*.yaml calcs/specs/
    make compute meta=calcs/specs/specs_ocean_v1.yaml
    make compute meta=calcs/specs/specs_ocean_v2.yaml
    make compute meta=calcs/specs/specs_ocean_v3.yaml

### "Collar" demo

collar visit:
  notes: |
    Enter the docker.
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/dataset-project-collar: dataset-project-collar
    ~/omicron/analyze-demo-collar: analyze-demo-collar
  visit: True

collar compute:
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-demo-collar/post: analyze-demo-collar-post
    ~/omicron/analyze-demo-collar/plot: analyze-demo-collar-plot
  collect files:
    specs_collar_demo.yaml: factory/calc/collar_demo/calcs/specs/collar_demo.yaml
  script: |
    cd factory/calc/collar_demo
    make compute

collar plots:
  notes: |
    Developing some commands!
  docker: basic
  where: ~/omicron/PIER
  mounts:
    ~/omicron/analyze-demo-collar/post: analyze-demo-collar-post
    ~/omicron/analyze-demo-collar/plot: analyze-demo-collar-plot
  collect files:
    specs_collar_demo.yaml: factory/calc/collar_demo/calcs/specs/collar_demo.yaml
  script: |
    cd factory/calc/collar_demo
    make plot undulations plot_height_profiles
    #! make plot undulations plot_undulation_spectra
    #make plot lipid_mesh plot_curvature_maps
"""
