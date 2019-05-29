from setuptools import setup

setup(name='kirallymanager',
      version='1.1',
      description='Management client for Gates Foundation ki rallies and sprints',
      long_description='Management client for Gates Foundation ki rallies and sprints',
      url='http://github.com/Sage-Bionetworks/ki-rally-manager',
      author='Kenneth Daily',
      author_email='kenneth.daily@sagebionetworks.org',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
      ],
      license='MIT',
      packages=['kirallymanager'],
      install_requires=[
          'pandas',
          'synapseclient'
      ],
      scripts=['bin/rallymanager'],
      zip_safe=False)
