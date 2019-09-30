from setuptools import setup, find_packages

setup(name='connect4_gym',
      author='Valentin-Bogdan Rosca',
      author_email='rosca.valentin2012@gmail.com',
      version='0.0.1',
      packages=find_packages(),
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.6",
      ],
      install_requires=[
          'gym',
          'pygame==1.9.3',
          'scikit-image==0.14.5',
          'numpy'
      ]
)
