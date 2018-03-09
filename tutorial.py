#!/usr/bin/env python

"""
Extensions to testset.py for tutorials.
Note that this was forked from testset.py and calls on that file.
"""

__all__ = ['interpreter']

def interpreter(**kwargs):
  """
  Interpret this file for the importing function.
  We indent with spaces because there is a lot of YAML in this file.
  """
  import os,re
  collect = {}
  # do something with incoming modifiers
  if 'mods' in kwargs and kwargs['mods']!=None:
    # incoming modifiers can act on text 
    mod_fn = kwargs.pop('mods')
    if not os.path.isfile(mod_fn): raise Exception('cannot find modifier file %s'%mod_fn)
    with open(mod_fn) as fp: text = fp.read()
    exec(text,collect)
  # collect modifiers
  text_changer = collect.pop('text_changer',lambda x:x)
  testset_processor = kwargs.pop('testset_processor',lambda x:x)
  if kwargs and any([i!=None for i in kwargs.values()]): print('[WARNING] unprocessed kwargs %s'%kwargs)
  # interpret the testsets
  try: import yaml
  except: raise Exception('testset needs yaml. install with `pip install --user pyyaml`')
  #! diverge from  testset.py interpreter function here
  #! we get the testset text and then perform replacements
  get_testset = {}
  #! absolute path
  with open('tests/testset.py') as fp: 
    exec(fp.read(),get_testset,get_testset)
  # note that the above gets you the testsets string from testset.py
  testsets = get_testset['testsets']
  testsets_demos = get_testset['testsets_demo_serve']
  names = 'b1 b2 b3 b4'.split()
  start_port,port_skip = 8010,4
  demo_ports = {'port':8008,'port_notebook':8009,'port_shell':8010}
  lab_spec,lab_tests = {},[]
  for lnum,name in enumerate(names):
    ports = {'port':start_port+port_skip*lnum,
      'port_notebook':start_port+port_skip*lnum+1,'port_shell':start_port+port_skip*lnum+2}
    new_test = str(testsets_demos)
    new_test = re.sub('factory shell','lab shell %s'%name,new_test)
    new_test = re.sub('demo serve','lab serve %s'%name,new_test)
    new_test = re.sub('demo:','project_%s:'%name,new_test)
    new_test = re.sub('connect_demo.yaml','connect_project_%s.yaml'%name,new_test)
    new_test = re.sub('PROJECT=demo','PROJECT=project_%s'%name,new_test)
    for key,val in ports.items(): new_test = re.sub(str(demo_ports[key]),str(val),new_test)
    lab_tests.append(new_test)
  tutorials = '\n\n'.join(lab_tests)
  # append the tutorials
  testsets = testsets + tutorials
  #! done modifying testsets here for the lab exercises
  # make substitutions
  testsets_subbed = str(testsets)
  global subs
  #! more modifications: including the docker spot here
  from config import read_config
  # get the root docker location from the config (set with `make set DOCKER_SPOT="<path>"`)
  # note also that you can use `@read_config('<key>')` in the YAML to look up keys from the config
  docker_spot = read_config('config.py')['DOCKER_SPOT']
  # global subsitutions in the text before YAML parsing
  subs = {'DOCKER_SPOT':docker_spot}
  #! done modifications for subs
  if subs!=None:
    for key,val in subs.items(): 
      testsets_subbed = re.sub(key,val,testsets_subbed)
  # interpret the YAML directions with the processor and the changer
  text_changed = text_changer(testsets_subbed)
  text_proc = testset_processor(text_changed)
  tests = yaml.load(text_proc)
  counts = dict([(key,sum([set(i)==set(key) for i in tests])) for key in tests])
  if any([v!=1 for v in counts.values()]):
    raise Exception('duplicate key sets: %s'%counts)
  # the dockerfile key points to variables in this script
  for key,val in tests.items():
    if 'script' in val:
      key_this = val['script']
      # you can define the script directly in the test or point to a global variable
      if key_this in globals(): val['script'] = text_changer(globals()[key_this])
  return tests
