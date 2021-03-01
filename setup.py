from pathlib import Path
from setuptools import setup, find_packages

readme = Path('README.md').read_text(encoding='utf-8')
readme = readme.replace('"https://raw.githubusercontent.com/alters-mit/magnebot/main/doc/images/reach_high.gif"',
                        '"https://github.com/alters-mit/magnebot/raw/main/social.jpg"')

setup(
    name='magnebot',
    version="1.0.3",
    description='High-level API for the Magnebot in TDW.',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/alters-mit/magnebot',
    author='Seth Alter',
    author_email="alters@mit.edu",
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    keywords='unity simulation tdw robotics',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['tdw>=1.8.0.0', 'numpy', 'ikpy', 'requests', 'matplotlib', 'pillow', "py_md_doc"],
)
