#!/usr/bin/env/python

from Cython.Distutils import build_ext
from setuptools import setup, Extension, find_packages

cmdclass = dict(build_ext=build_ext)

av_files = [
 '_core',
 'container',
 'format',
 'frame',
 'logging',
 'packet',
 'plane',
 'stream',
 'utils']

av_video_files = ['format', 'frame', 'plane', 'stream', 'swscontext']
av_audio_files = ['fifo', 'format', 'frame', 'layout', 'plane', 'resampler', 'stream']
av_subtitles_files = ['stream', 'subtitle']

av_extensions = [Extension('av.' + f, sources=['av/{0}.pyx'.format(f)], language='c', include_dirs=['av', '.', 'include'], depends=['av/{0}.pxd'.format(f)]) for f in av_files]

av_video_extensions = [Extension('av.video.' + f, sources=['av/video/{0}.pyx'.format(f)], language='c', include_dirs=['av/video', '.', 'include'], depends=['av/video/{0}.pxd'.format(f)]) for f in av_video_files]

av_audio_extensions = [Extension('av.audio.' + f, sources=['av/audio/{0}.pyx'.format(f)], language='c', include_dirs=['av/audio', '.', 'include'], depends=['av/audio/{0}.pxd'.format(f)]) for f in av_audio_files]

av_subtitles_extensions = [Extension('av.subtitles.' + f, sources=['av/subtitles/{0}.pyx'.format(f)], language='c', include_dirs=['av/subtitles', '.', 'include'], depends=['av/subtitles/{0}.pxd'.format(f)]) for f in av_subtitles_files]


setup(
    name='av',
    ext_modules = av_extensions + av_video_extensions + av_audio_extensions + av_subtitles_extensions,
    packages=find_packages(exclude=['build*', 'tests*', 'examples*']),
    cmdclass=cmdclass
)
