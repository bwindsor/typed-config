from pathlib import Path
from setuptools import setup
from typedconfig.__version__ import __version__

# The text of the README file
readme_text = Path(__file__).with_name("README.md").read_text()

setup(
    name='typed-config',
    version=__version__,
    description='Typed, extensible, dependency free configuration reader for Python projects for multiple config sources and working well in IDEs for great autocomplete performance.',
    long_description=readme_text,
    long_description_content_type='text/markdown',
    url='https://github.com/bwindsor/typed-config',
    author='Ben Windsor',
    author_email='',
    python_requires='>=3.6.0',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development',
        'Typing :: Typed',
    ],
    packages=['typedconfig'],
    include_package_data=True,
    install_requires=[],
    entry_points={}
)
