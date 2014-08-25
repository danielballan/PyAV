from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from subprocess import Popen, PIPE
import ctypes.util
import errno
import os
import re
import platform


if platform.system() == 'Windows':
    raise NotImplementedError("PyAV cannot currently be built on Windows.")
    # Whatever approach we take on Windows, it will not require pkgconfig.
else:
    try:
        import pkgconfig
    except ImportError:
        raise ImportError("On Unix-based systems, the Python package "
                          "'pkgconfig' is required to setup PyAV.")


version = '0.1.0'
required_libs = ['libavformat', 'libavcodec', 'libavutil', 'libswscale']
resample_libs = ['libswresample', 'libavresample']  # require one


# The "extras" to be supplied to every one of our modules.
extension_extra = {
    'include_dirs': ['include'],
}
config_macros = [
    ("PYAV_VERSION", version),
]


class LibraryNotFoundError(Exception):
    pass


# Get the config for the libraries that we require.
for lib_name in required_libs:
    missing = []
    if pkgconfig.exists(lib_name):
        config_macros.append(('PYAV_HAVE_' + lib_name.upper(), '1'))
    else:
        missing.append(lib_name)
if missing:
    raise LibraryNotFoundError(
        "Could not find the required libraries: {0}".format(
            ' '.join(missing)))

for lib_name in resample_libs:  # require one
    if pkgconfig.exists(lib_name):
        config_macros.append(('PYAV_HAVE_' + lib_name.upper(), '1'))
    else:
        missing.append(lib_name)
if len(missing) > 1:
    raise LibraryNotFoundError(
        "Could not find either of these libraries: {0}."
        "One or the other is required.".format(' '.join(missing)))

pkg_info = pkgconfig.parse(' '.join(required_libs + resample_libs))
pkg_info = {k: list(v) for k, v in pkg_info.items()}  # dict of lists
extension_extra.update(pkg_info)


def check_for_func(lib_names, func_name):
    """Define macros if we can find the given function in one of the given libraries."""

    for lib_name in lib_names:

        lib_path = ctypes.util.find_library(lib_name)
        if not lib_path:
            print 'Could not find', lib_name, 'with ctypes.util.find_library'
            continue

        # Open the lib. Look in the path returned by find_library, but also all
        # the paths returned by pkg-config (since we don't get an absolute path
        # on linux).
        lib_paths = [lib_path]
        lib_paths.extend(
            os.path.join(root, os.path.basename(lib_path))
            for root in set(extension_extra.get('library_dirs', []))
        )
        for lib_path in lib_paths:
            try:
                lib = ctypes.CDLL(lib_path)
                break
            except OSError:
                pass
        else:
            print 'Could not find', lib_name, 'with ctypes; looked in:'
            print '\n'.join('\t' + path for path in lib_paths)
            continue


        if hasattr(lib, func_name):
            extension_extra.setdefault('define_macros', []).append(('HAVE_%s' % func_name.upper(), '1'))
            return


# Check for some specific functions.
for libs, func in (
    (['avcodec', 'avutil', 'avcodec'], 'av_frame_get_best_effort_timestamp'),
    (['avformat'], 'avformat_close_input'),
    (['avformat'], 'avformat_alloc_output_context2'),
    (['avutil'], 'av_calloc'),
):
    if check_for_func(libs, func):
        config_macros.append(('PYAV_HAVE_' + func.upper(), '1'))


# Construct the modules that we find in the "build/cython" directory.
ext_modules = []
build_dir = os.path.abspath(os.path.join(__file__, '..', 'src'))
for dirname, dirnames, filenames in os.walk(build_dir):
    for filename in filenames:
        if filename.startswith('.') or os.path.splitext(filename)[1] != '.c':
            continue

        path = os.path.join(dirname, filename)
        name = os.path.splitext(os.path.relpath(path, build_dir))[0].replace('/', '.')

        ext_modules.append(Extension(
            name,
            sources=[path],
            **extension_extra
        ))


class my_build_ext(build_ext):

    def run(self):

        include_dir = os.path.join(self.build_temp, 'include')
        pyav_dir = os.path.join(include_dir, 'pyav')
        try:
            os.makedirs(pyav_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        header_path = os.path.join(pyav_dir, 'config.h')
        print 'writing', header_path
        with open(header_path, 'w') as fh:
            fh.write('#ifndef PYAV_COMPAT_H\n')
            fh.write('#define PYAV_COMPAT_H\n')
            for k, v in config_macros:
                fh.write('#define %s %s\n' % (k, v))
            fh.write('#endif\n')

        self.include_dirs = self.include_dirs or []
        self.include_dirs.append(include_dir)

        return build_ext.run(self)


setup(

    name='av',
    version=version,
    description='Pythonic bindings for libav.',
    
    author="Mike Boers",
    author_email="pyav@mikeboers.com",
    
    url="https://github.com/mikeboers/PyAV",

    install_requires=['pkgconfig'],
    packages=find_packages(exclude=['build*', 'tests*', 'examples*']),
    
    zip_safe=False,
    ext_modules=ext_modules,

    cmdclass={'build_ext': my_build_ext},

)
