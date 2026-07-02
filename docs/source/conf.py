import os
import sys
sys.path.insert(0, os.path.abspath('../..'))


project = 'API Reference'
copyright = '2026, Engineering Team'
author = 'Engineering Team'

# Enable automatic documentation generation and markdown exporting
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Supports Google/NumPy style docstrings
    'sphinx.ext.viewcode',   # Links to code blocks
    'sphinx_markdown_builder' # Exports to .md instead of .html
]

# Configure markdown outputs to feel native to Obsidian
markdown_anchor_sections = True
markdown_docutils_classes = False

master_doc = 'modules'

