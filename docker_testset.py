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
	"""
	import os
	collect = {}
	#---do something with incoming modifiers
	if 'mods' in kwargs: 
		#---incoming modifiers can act on text 
		mod_fn = kwargs.pop('mods')
		if not os.path.isfile(mod_fn): raise Exception('cannot find modifier file %s'%mod_fn)
		with open(mod_fn) as fp: text = fp.read()
		exec(text,collect)
	#---collect modifiers
	text_changer = collect.get('text_changer',lambda x:x)
	if kwargs: print('[WARNING] unprocessed kwargs %s'%kwargs)
	#---interpret the testsets
	import yaml
	tests = yaml.load(text_changer(testsets))
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

###---SCRIPTS

test_script_factory_setup = """#!/bin/bash
set -e
git clone http://github.com/biophyscode/factory factory
cd factory
make nuke sure
make set species anaconda
make set anaconda_location=~/Miniconda3-latest-Linux-x86_64.sh
make set automacs="http://github.com/biophyscode/automacs"
make set omnicalc="http://github.com/biophyscode/omnicalc"
cp ~/reqs_conda.yaml .
cp ~/reqs_pip.txt .
make set reqs_conda reqs_conda.yaml
make set reqs_pip reqs_pip.txt
make setup
"""

###---TESTSETS

testsets = """

factory setup:
  notes: |
    This test will create a blank factory for other tests.
    It includes custom requirements for anaconda which exclude Mayavi which is not compiling on the debian docker.
    This test should only be run once, while connection tests can be rerun until the connection is right.
    After you have a factory and a connection you can run the compute tests below.
  # which docker to use
  docker: basic
  # prevent rerun by logging to docker.json
  once: True
  # external location for running the factory
  where: ~/omicron/PIER
  # which dockerfile variable to execute
  script: test_script_factory_setup
  # custom preparation script
  collect requirements: >
    cp ~/libs/Miniconda3-latest-Linux-x86_64.sh ~/omicron/PIER/Miniconda3-latest-Linux-x86_64.sh
  # local files to copy to where
  collect files:
    reqs_conda_factory_setup.yaml: reqs_conda.yaml
    reqs_pip_factory_setup.txt: reqs_pip.txt

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
    #!/bin/bash
    set -e
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
    #!/bin/bash
    set -e
    cd factory/calc/ptdins
    cp ~/specs_ptdins_v*.yaml calcs/specs/
    make compute meta=calcs/specs/specs_ptdins_v1.yaml

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
    #!/bin/bash
    set -e
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
    #!/bin/bash
    set -e
    cd factory/calc/ocean
    cp ~/specs_ocean_v*.yaml calcs/specs/
    make compute meta=calcs/specs/specs_ocean_v1.yaml
    make compute meta=calcs/specs/specs_ocean_v2.yaml
    make compute meta=calcs/specs/specs_ocean_v3.yaml

"""
