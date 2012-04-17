#!/usr/bin/env python
from setuptools import setup,find_packages

METADATA = dict(
    name='django-scrobble',
    version='0.1.0',
    author='Chris Priest',
    author_email='cp368202@ohiou.edu',
    description='Integration with last.fm scrobble api',
    #long_description=open('README.md').read(),
    url='http://github.com/priestc/django-scrobble',
    keywords='lastfm scrobble django',
    install_requires=['django', 'requests'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    packages=find_packages(),
)

if __name__ == '__main__':
    setup(**METADATA)
    
