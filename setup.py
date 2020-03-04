from setuptools import setup, find_packages
from distutils.core import setup


setup(
    name='labelpix',
    version='1.0.0',
    packages=find_packages(),
    package_dir={'': 'Object Detection Utils/labelpix'},
    url='https://github.com/emadboctorx/labelpix',
    license='MIT',
    author='emadboctor',
    author_email='eboctor0@gmail.com',
    description='Labeling tool for object detection', install_requires=['PyQt5'],
    long_description=open('README.md').read()
)
