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
  import yaml
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

subs = {'DOCKER_SPOT':'~/omicron/PIER2'}

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
    rm -rf ~/host/holding

"""

testsets_collar = """

collar connect:
  notes: |
    Generate the omnicalc instance that points to the simulation data.
  docker: small-p2
  where: DOCKER_SPOT
  mounts:
    ~/omicron/dataset-project-collar: dataset-project-collar
    ~/omicron/analyze-demo-collar: analyze-demo-collar
  report files: ['connect_collar_demo.yaml']
  collect files:
    connect_collar_demo.yaml: factory/connections/connect_collar_demo.yaml
  script: cd host/factory && make connect collar_demo

collar compute:
  docker: small-p2
  where: DOCKER_SPOT
  mounts:
    ~/omicron/analyze-demo-collar/post: analyze-demo-collar-post
    ~/omicron/analyze-demo-collar/plot: analyze-demo-collar-plot
  report files: ['specs_collar_demo.yaml','art_collar.py']
  collect files:
    specs_collar_demo.yaml: factory/calc/collar_demo/calcs/specs/collar_demo.yaml
    art_collar.py: factory/calc/collar_demo/calcs/art_collar.py
  script: cd host/factory/calc/collar_demo && make compute

collar plots:
  docker: small-p2
  where: DOCKER_SPOT
  mounts:
    ~/omicron/analyze-demo-collar/post: analyze-demo-collar-post
    ~/omicron/analyze-demo-collar/plot: analyze-demo-collar-plot
  collect files:
    specs_collar_demo.yaml: host/factory/calc/collar_demo/calcs/specs/collar_demo.yaml
    art_collar.py: host/factory/calc/collar_demo/calcs/art_collar.py
  script: |
    cd host/factory/calc/collar_demo
    make set mpl_agg=True
    make plot undulations plot_height_profiles
    make plot undulations undulation_spectra
    make plot lipid_mesh plot_curvature_maps
    make plot curvature_undulation_coupling individual_reviews

"""

testsets_banana = """

banana connect:
  docker: small-p2
  where: DOCKER_SPOT
  report files: ['connect_banana.yaml']
  collect files: 
    connect_banana.yaml: factory/connections/connect_banana.yaml
  mounts:
    /store-sigma/yards/DATA/analyze-project-banana/post: analyze-project-banana-post
    /store-sigma/yards/DATA/analyze-project-banana/plot: analyze-project-banana-plot
    /store-sigma/yards/DATA/dataset-project-banana: dataset-project-banana
  script: cd ~/host/factory && make connect banana

banana compute:
  docker: small-p4
  where: DOCKER_SPOT
  report files: ['specs_banana.yaml']
  collect files: 
    automacs.py: ".automacs.py"
    specs_banana.yaml: factory/calc/banana/calcs/specs/specs_banana.yaml
  mounts:
    /store-sigma/yards/DATA/analyze-project-banana/post: analyze-project-banana-post
    /store-sigma/yards/DATA/analyze-project-banana/plot: analyze-project-banana-plot
    /store-sigma/yards/DATA/dataset-project-banana: dataset-project-banana
  script: |
    cd ~/host/factory/calc/banana
    make unset meta_filter && make set meta_filter specs_banana.yaml
    make compute

"""

#---concatenate the testsets
testsets = testsets_general + testsets_collar + testsets_banana
