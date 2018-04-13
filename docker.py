#!/usr/bin/env/python

"""
Consolidated docker settings.
See the interpreter function below.
This file should be processed by its own interpreter function.
Note that this file works closely with docks/docks.py.
"""

__all__ = ['interpreter']

local_config_fn = 'config.py'

def interpreter(**kwargs):
	"""
	Interpret this file for the importing function.
	The docker config for the pier must supply: a list of dockerfiles, requirements on disk for those files,
	and a list of testsets.
	Note that you can manipulate the testsets with the mods argument which reads a "text_changer" from an
	external script or you can call on the config using the testset_processor.
	"""
	import os,re,sys
	str_types = [str,unicode] if sys.version_info<(3,0) else [str]
	# modification sequence
	collect = {}
	# do something with incoming modifiers
	if 'mods' in kwargs and kwargs['mods']!=None: 
		# incoming modifiers can act on text 
		mod_fn = kwargs.get('mods')
		if not os.path.isfile(mod_fn): raise Exception('cannot find modifier file %s'%mod_fn)
		with open(mod_fn) as fp: text = fp.read()
		eval(compile(text,'<string>','exec'),globals(),collect)
	global requirements,sequences,dockerfiles,local_config_fn
	# collect modifiers
	text_changer = collect.get('text_changer',lambda x:x)
	if kwargs and any([i!=None for i in kwargs.values()]): print('[WARNING] unprocessed kwargs %s'%kwargs)
	# process this file with modifications
	dockerfiles = {}
	dockerfile_variable_regex = '^dockerfile_(.+)'
	for key in globals():
		if re.match(dockerfile_variable_regex,key):
			# if mods apply text_changer to docker scripts
			text = text_changer(str(globals()[key]))
			dockerfiles[re.match(dockerfile_variable_regex,key).group(1)] = text
	instruct = dict(dockerfiles=dockerfiles,requirements=requirements,sequences=dict(sequences))
	# get testsets from external files
	testset_sources = globals().get('testset_sources',[])
	# if testset sources is empty we can set it with `make set docks_testsets <path>` where the path
	# ... is local to this docker configuration file
	warn_no_tests = ('[WARNING] no testsets. either add paths to the testset_sources list or run '+
		'`make set docks_testset_sources <path>` where the path is local to the docker config')
	try:
		config_fn = os.path.join(os.getcwd(),local_config_fn)
		with open(local_config_fn) as fp: config = eval(fp.read())
		testset_sources = config.get('docks_testset_sources',[])
		if type(testset_sources) in str_types: testset_sources = [testset_sources]
	except: print(warn_no_tests)
	if testset_sources == []: print(warn_no_tests)
	# testset sources update the instruction set sequentially
	for source in testset_sources: 
		# sources are local to this file
		source_fn = os.path.join(os.path.dirname(__file__),source)
		if not os.path.isfile(source_fn):
			raise Exception('missing testset source %s'%source_fn)
		with open(source_fn) as fp: code = fp.read()
		mod_this = {}
		eval(compile(code,'<string>','exec'),globals(),mod_this)
		if 'tests' not in instruct: instruct['tests'] = {}
		def testset_processor(text):
			"""Get information from the root config.py if necessary. Only works with top-level keys."""
			import os,re
			comp = re.compile(r'@read_config\((.*?)\)',flags=re.M)
			if comp.search(text):
				config_fn = os.path.join(os.getcwd(),local_config_fn)
				with open(local_config_fn) as fp: config = eval(fp.read())
				def subber(key): 
					"""Substitute values from the config."""
					this_key = eval(key.group(1))
					if type(this_key)==tuple and len(this_key)!=1: 
						raise Exception('not prepared for tuple in read_config yet: see "%s"'%str(this_key))
					elif type(this_key)==tuple: this_key = this_key[0]
					if this_key not in config:
						raise Exception('failed to find %s in the config at %s'%(this_key,config_fn))
					return config[this_key]
				text = comp.sub(subber,text)
			return text
		if 'testset_processor' in kwargs: raise Exception('kwargs already has a testset_processor')
		else: kwargs.update(testset_processor=testset_processor)
		instruct['tests'].update(**mod_this['interpreter'](**kwargs))
	return instruct

### SERIES 2 (current)

dockerfile_stretch = """
FROM debian:stretch
"""

dockerfile_debian_minimal_start = """
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y git make wget 
RUN apt-get install -y git vim
RUN apt-get install -y python
"""

dockerfile_debian_compilers = """
RUN apt-get install -y cmake
RUN apt-get install -y build-essential
"""

dockerfile_gromacs = """
WORKDIR /root
RUN apt-get install -y libfftw3-dev
RUN wget ftp://ftp.gromacs.org/pub/gromacs/gromacs-5.1.2.tar.gz
RUN tar xvf gromacs-5.1.2.tar.gz
RUN rm gromacs-5.1.2.tar.gz
WORKDIR /root/gromacs-5.1.2
RUN mkdir build
WORKDIR /root/gromacs-5.1.2/build
RUN cmake /root/gromacs-5.1.2
RUN make -j 4
RUN make install
WORKDIR /root
"""

dockerfile_debian_apache = """
WORKDIR /root/
RUN apt-get install -y apache2
RUN apt-get install -y apache2-dev
"""

dockerfile_debian_vmd = """
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y libglu1 libxinerama1 libxi6 libgconf-2-4 imagemagick
WORKDIR /root
COPY VMD_SOURCE /root/
RUN mkdir vmd-latest
RUN tar xvf VMD_SOURCE -C vmd-latest --strip-components=1
WORKDIR /root/vmd-latest
RUN ./configure
WORKDIR /root/vmd-latest/src
RUN make install
"""

dockerfile_debian_ffmpeg = """
WORKDIR /root/
RUN echo "deb http://www.deb-multimedia.org stretch main non-free" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install --allow-unauthenticated -y deb-multimedia-keyring 
RUN apt-get update
RUN apt-get install -y ffmpeg x264
"""

dockerfile_debian_gotty = """
WORKDIR /root/
RUN mkdir /usr/local/gotty
WORKDIR /usr/local/gotty
RUN wget https://github.com/yudai/gotty/releases/download/v1.0.1/gotty_linux_amd64.tar.gz
RUN tar xvf gotty_linux_amd64.tar.gz
"""

dockerfile_debian_node = """
WORKDIR /root/
RUN apt-get install curl
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install nodejs npm
WORKDIR /root/
"""

dockerfile_debian_sshd = """
WORKDIR /root/
RUN apt-get install -y openssh-server
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
EXPOSE 22
RUN useradd -m @USER
RUN usermod -s /bin/bash @USER
RUN echo @USER:@read_config('user_creds') |chpasswd
ENTRYPOINT service ssh restart && sleep infinity
"""

"""
need to develop: 
"""

### REQUIREMENTS

requirements = {
	'debian_vmd':{
		'config_keys':'location_vmd_source','filename_sub':'VMD_SOURCE'},}

### SEQUENCES

"""
if you modify the sequences below you may need to expunge and quickly rebuild the containers 
with any necessary additions. this can be done with `make unset docker_history` followed by
`make docker <name>` where name is the first key in the tuples below
note that sometimes the images can get cluttered so try this command to clean them up:
docker rmi $(docker images | awk '$1 ~ /-s/ {print $3}')

deployment note for opensuse: prepare_server fails until you run: sudo zypper install apache2-mod_wsgi 
and it also installs apache2 apache2-mod_wsgi apache2-prefork apache2-utils git-web libnghttp2-14 
then install sudo zypper install apache2-devel
"""

sequences = [
	# MINIMAL IMAGE BUILT IN STEPS
	('small-p1',{'seq':'stretch',}),
	# projects that already have gromacs trajectories only require part two (p2)
	('small-p2',{'seq':'stretch debian_minimal_start','user':True}),
	('small-p3','stretch debian_minimal_start debian_compilers'),
	# projects that need gromacs for slicing require p4
	('small-p4',{'seq':'stretch debian_minimal_start debian_compilers gromacs',
		'user':True,'coda':'RUN echo "source /usr/local/gromacs/bin/GMXRC.bash" >> ~/.bashrc'}),
	# demo with no visualization requires p5
	('small-p5',{'seq':'stretch debian_minimal_start debian_compilers gromacs debian_apache',
		'user':True,'coda':'RUN echo "source /usr/local/gromacs/bin/GMXRC.bash" >> ~/.bashrc'}),
	# demo with visualization
	('small-p6',{'seq':'stretch debian_minimal_start debian_compilers gromacs debian_apache '+
		'debian_vmd debian_ffmpeg',
		'user':True,'coda':'RUN echo "source /usr/local/gromacs/bin/GMXRC.bash" >> ~/.bashrc'}),
	# the complete docker includes a sequential docker built with GROMACS, VMD, ffmpeg, and gotty
	('small-p7',{'seq':
		'stretch debian_minimal_start debian_compilers gromacs debian_apache '+
		'debian_vmd debian_ffmpeg debian_gotty',
		'user':True,'coda':'\n'.join([
			'RUN echo "export TERM=xterm" >> ~/.bashrc',
			'RUN echo "source /usr/local/gromacs/bin/GMXRC.bash" >> ~/.bashrc',])}),
	# the sshd docker must be run with the sshd testset item to handle user credentials
	('sshd',{'seq':'stretch debian_minimal_start debian_sshd','user':False}),
	# alias for the complete docker, which is given above by small-p7
	('biophyscode_demo',{'seq':
		'stretch debian_minimal_start debian_compilers gromacs debian_apache '+
		'debian_vmd debian_ffmpeg debian_gotty',
		'user':True,'coda':'\n'.join([
			'RUN echo "export TERM=xterm" >> ~/.bashrc',
			'RUN echo "source /usr/local/gromacs/bin/GMXRC.bash" >> ~/.bashrc',])}),]
