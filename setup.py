import os
from setuptools import setup
from isp import VERSION

f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
readme = f.read()
f.close()

setup(
    name='isp-pyplugin',
    version=".".join(map(str, VERSION)),
    description='Small lib helps writing Plugins for ISP System products',
    long_description=readme,
    author="Pavel Shiryaev",
    author_email='pws@front.ru',
    url='http://github.com/pws21/ips-pyplugin',
    py_modules=['isp'],
    install_requires=['setuptools','lxml'],
    zip_safe=False,
    classifiers=[
    'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
