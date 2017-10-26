#!/usr/bin/env/python

"""
Consolidated docker settings.
See the interpreter function below.
This file should be processed by its own interpreter function.
"""

__all__ = ['interpreter']

def interpreter(**kwargs):
	"""
	Interpret this file for the importing function.
	The docker config for the pier must supply:
	-- a list of dockerfiles
	-- requirements on disk for those files
	-- a list of testsets
	"""
	import os,re
	#---modification sequence
	collect = {}
	#---do something with incoming modifiers
	if 'mods' in kwargs: 
		#---incoming modifiers can act on text 
		mod_fn = kwargs.get('mods')
		if not os.path.isfile(mod_fn): raise Exception('cannot find modifier file %s'%mod_fn)
		with open(mod_fn) as fp: text = fp.read()
		exec(text,collect)
	global requirements,sequences,dockerfiles
	#---collect modifiers
	text_changer = collect.get('text_changer',lambda x:x)
	if kwargs: print('[WARNING] unprocessed kwargs %s'%kwargs)
	#---process this file with modifications
	dockerfiles = {}
	dockerfile_variable_regex = '^dockerfile_(.+)'
	for key in globals():
		if re.match(dockerfile_variable_regex,key):
			#---if mods apply text_changer to docker scripts
			text = text_changer(str(globals()[key]))
			dockerfiles[re.match(dockerfile_variable_regex,key).group(1)] = text
	#---apply text_changer to requirements
	requirements = dict([(key,[text_changer(j) for j in val]) for key,val in requirements.items()])
	instruct = dict(dockerfiles=dockerfiles,requirements=requirements,sequences=dict(sequences))
	#---get testsets from external files
	testset_sources = globals().get('testset_sources',[])
	#---testset sources update the instruction set sequentially
	for source in testset_sources: 
		#---sources are local to this file
		source_fn = os.path.join(os.path.dirname(__file__),source)
		if not os.path.isfile(source_fn):
			raise Exception('missing testset source %s'%source_fn)
		with open(source_fn) as fp: code = fp.read()
		mod_this = {}
		exec(code,mod_this)
		if 'tests' not in instruct: instruct['tests'] = {}
		instruct['tests'].update(**mod_this['interpreter'](**kwargs))
	return instruct


###---DOCKERFILES

dockerfile_jessie = """
FROM debian:jessie
"""

dockerfile_debian_start = """
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y build-essential wget openssh-server apt-utils
RUN apt-get install -y make cmake git vim screen
RUN apt-get install -y libfftw3-dev libxml2-dev
RUN apt-get install -y python
"""

dockerfile_gromacs = """
WORKDIR /root
RUN wget ftp://ftp.gromacs.org/pub/gromacs/gromacs-5.1.2.tar.gz
RUN tar xvf gromacs-5.1.2.tar.gz
RUN rm gromacs-5.1.2.tar.gz
WORKDIR /root/gromacs-5.1.2
RUN mkdir build
WORKDIR /root/gromacs-5.1.2/build
RUN cmake /root/gromacs-5.1.2 -DGMX_USE_RDTSCP=OFF
RUN make -j 4
RUN make install
WORKDIR /root
RUN echo "source /usr/local/gromacs/bin/GMXRC.bash" >> ~/.bashrc
"""

dockerfile_debian_python = """
ARG DEBIAN_FRONTEND=noninteractive
#---standard packages
RUN apt-get install -y python-tk
RUN apt-get install -y python 
RUN apt-get install -y python-dev 
RUN apt-get install -y python-numpy 
RUN apt-get install -y python-numpy-dev
RUN apt-get install -y python-scipy
RUN apt-get install -y redis-server
RUN apt-get install -y python-h5py
RUN apt-get install -y python-virtualenv
#---pip packages
RUN apt-get install -y python-pip
RUN pip install MDAnalysis
"""

dockerfile_debian_vmd = """
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y libglu1 libxinerama1 libxi6 libgconf-2-4 imagemagick
WORKDIR /root/
COPY vmd-1.9.1.bin.LINUXAMD64.opengl.tar /root/
RUN tar xvf vmd-1.9.1.bin.LINUXAMD64.opengl.tar
WORKDIR /root/vmd-1.9.1
RUN ./configure
WORKDIR /root/vmd-1.9.1/src
RUN make install
"""

dockerfile_debian_ffmpeg = """
WORKDIR /root/
RUN echo "deb http://www.deb-multimedia.org jessie main non-free" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install --force-yes -y deb-multimedia-keyring 
RUN apt-get update
RUN apt-get install -y ffmpeg x264
"""

dockerfile_anaconda2 = """
COPY Anaconda2-4.2.0-Linux-x86_64.sh /root/
WORKDIR /root/
RUN bash Anaconda2-4.2.0-Linux-x86_64.sh -b -p /usr/local/anaconda2
ENV PATH=/usr/local/anaconda2/bin:$PATH
RUN pip install numpy
RUN pip install scipy
RUN pip install MDAnalysis
"""

dockerfile_anaconda3 = """
COPY Anaconda3-4.2.0-Linux-x86_64.sh /root/
WORKDIR /root/
RUN bash Anaconda3-4.2.0-Linux-x86_64.sh -b -p /usr/local/anaconda3
"""

###---REQUIREMENTS

requirements = {
	'dockerfile_anaconda2':['~/libs/Anaconda2-4.2.0-Linux-x86_64.sh'],
	'dockerfile_anaconda3':['~/libs/Anaconda3-4.2.0-Linux-x86_64.sh'],
	'dockerfile_debian_vmd':['~/libs/vmd-1.9.1.bin.LINUXAMD64.opengl.tar'],
	'dockerfile_factory':['~/libs/'],}

###---SEQUENCES

sequences = [
	('simple','jessie debian_start gromacs'),
	('simple_vmd','jessie debian_start gromacs debian_vmd'),
	('simple_vmd_ffmpeg','jessie debian_start gromacs debian_vmd debian_ffmpeg'),
	#---basic is an alias for simple with VMD and FFMPEG and serves as a starting point for the factory
	('basic','jessie debian_start gromacs debian_vmd debian_ffmpeg'),]

###---TESTSETS

testset_sources = ['docker_testset.py']
