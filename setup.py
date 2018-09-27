from setuptools import setup

setup(name='hbgdkirallymanager',
      version='0.1',
      description='Management client for HBGDki rallies and sprints',
      long_description='Management client for Healthy Birth Growth and Development Knowledge Initiative (HBGDki) rallies and sprints',
      url='http://github.com/Sage-Bionetworks/hbgdkibootstrap',
      author='Kenneth Daily',
      author_email='kenneth.daily@sagebionetworks.org',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
      ],
      license='MIT',
      packages=['hbgdkirallymanager'],
      install_requires=[
          'pandas',
          'synapseclient'
      ],
      scripts=['bin/rallymanager'],
      zip_safe=False)
