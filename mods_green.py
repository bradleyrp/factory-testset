#!/usr/bin/env python

subs = [
	('~/omicron/PIER','/home/ryb/PIER'),
	('~/libs/Miniconda3-latest-Linux-x86_64.sh',
		'~/libs/Miniconda3-latest-Linux-x86_64.sh'),
	('~/libs/vmd-1.9.1.bin.LINUXAMD64.opengl.tar',
		'~/factory/sources/vmd-1.9.1.bin.LINUXAMD64.opengl.tar'),]

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
