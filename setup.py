from setuptools import setup

setup(name='hbgdkibootstrap',
      version='0.1',
      description='Bootstrap scripts for HBGDki rallies and sprints',
      long_description='Bootstrap scripts for Healthy Birth Growth and Development Knowledge Initiative (HBGDki) rallies and sprints',
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
      packages=['hbgdkibootstrap'],
      install_requires=[
          'pandas',
          'synapseclient'
      ],
      scripts=['bin/bootstrap-rally-sprint'],
      zip_safe=False)
