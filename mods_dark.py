#!/usr/bin/env python

subs = [
	('DATA_ROOT','~/omicron'),
	('SPOT_MINICONDA','~/libs/Miniconda3-latest-Linux-x86_64.sh'),
	('SPOT_VMD','~/libs/vmd-1.9.1.bin.LINUXAMD64.opengl.tar'),]

def text_changer(text):
	"""
	Make regex substitutions in the testset configuration files.
	"""
	import re
	global subs
	for match,sub in subs:
		comp = re.compile(match,flags=re.M+re.DOTALL)
		text = comp.sub(sub,text)
	return text
