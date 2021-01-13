from setuptools import setup, find_packages


setup(
    name='magnebot',
    version="0.2.3",
    description='High-level API for the Magnebot in TDW.',
    long_description='High-level API for the Magnebot in TDW.',
    url='https://github.com/alters-mit/magnebot',
    author='Seth Alter',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    keywords='unity simulation tdw',
    packages=find_packages(),
    install_requires=['tdw', 'numpy', 'ikpy', 'matplotlib', 'pillow', "py_md_doc"],
)
