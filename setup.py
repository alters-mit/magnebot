from setuptools import setup, find_packages


setup(
    name='magnebot',
    version="1.0.0.0",
    description='High-level API for the Magnebot in TDW.',
    long_description='High-level API for the Magnebot in TDW.',
    url='https://github.com/alters-mit/magnebot',
    author='Seth Alter',
    author_email="alters@mit.edu",
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
    keywords='unity simulation tdw robotics',
    packages=find_packages(),
    install_requires=['tdw>=1.8.0.0', 'numpy', 'ikpy', 'requests', 'matplotlib', 'pillow', "py_md_doc"],
)
