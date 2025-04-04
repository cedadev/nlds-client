# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html



import os
import sys
sys.path.insert(0, os.path.abspath('../../../'))

from nlds_client import __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = 'Near-Line Data Store Client'
copyright = '2025, Centre for Environmental Data Analysis, Science and Technologies Facilities Council, UK Research and Innovation'
author = 'Neil Massey & Jack Leland'

version = __version__
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx_click']

templates_path = ['_templates']
exclude_patterns = []
html_favicon = '_images/icon-black.png'



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_logo = "_images/nlds.png"
html_theme_options = {
    'logo_only': False,
    'display_version': True,
}