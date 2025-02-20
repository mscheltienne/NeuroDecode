# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import inspect
import subprocess
import sys
from datetime import date
from importlib import import_module
from pathlib import Path

import mne
from intersphinx_registry import get_intersphinx_mapping
from sphinx_gallery.sorting import FileNameSortKey

import mne_lsl

# -- path setup ------------------------------------------------------------------------
sys.path.append(str(Path(__file__).parent / "_sphinxext"))

# -- project information ---------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MNE-LSL"
author = "M. Scheltienne, A. Desvachez, K. Lee"
copyright = f"{date.today().year}, {author}"  # noqa: A001
release = mne_lsl.__version__
package = mne_lsl.__name__
gh_url = "https://github.com/mne-tools/mne-lsl"

# -- mne information -------------------------------------------------------------------

gh_url_mne = "https://github.com/mne-tools/mne-python"
release_mne = mne.__version__

# -- general configuration -------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = "5.0"

# The document name of the “root” document, that is, the document that contains the root
# toctree directive.
root_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be extensions coming
# with Sphinx (named "sphinx.ext.*") or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "numpydoc",
    "sphinxcontrib.bibtex",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
    "sphinx_issues",
    # local extensions
    "sphinx_remove_toctrees",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# Sphinx will warn about all references where the target cannot be found.
nitpicky = True
nitpick_ignore = []

# A list of ignored prefixes for module index sorting.
modindex_common_prefix = [f"{package}."]

# The name of a reST role (builtin or Sphinx extension) to use as the default role, that
# is, for text marked up `like this`. This can be set to 'py:obj' to make `filter` a
# cross-reference to the Python function “filter”.
default_role = "py:obj"

# list of warning types to suppress
suppress_warnings = ["config.cache"]

# -- options for HTML output -----------------------------------------------------------
html_css_files = [
    "css/style.css",
]
html_favicon = "_static/logos/logo-no-mne.svg"
html_logo = "_static/logos/logo-mne-hex.svg"
html_permalinks_icon = "🔗"
html_show_sphinx = False
html_static_path = ["_static"]
html_theme = "furo"
html_title = project

# Documentation to change footer icons:
# https://pradyunsg.me/furo/customisation/footer/#changing-footer-icons
html_theme_options = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": gh_url,
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,  # noqa: E501
            "class": "",
        },
    ],
    "sidebar_hide_name": True,
}

# -- autosummary -----------------------------------------------------------------------
autosummary_generate = True

# -- autodoc ---------------------------------------------------------------------------
autodoc_typehints = "none"
autodoc_member_order = "groupwise"
autodoc_warningiserror = True
autoclass_content = "class"

# -- intersphinx -----------------------------------------------------------------------
intersphinx_mapping = get_intersphinx_mapping(
    packages={"matplotlib", "mne", "numpy", "python", "scipy", "sklearn"}
)
intersphinx_timeout = 5

# -- sphinx-issues ---------------------------------------------------------------------
issues_github_path = gh_url.split("https://github.com/")[-1]

# -- autosectionlabels -----------------------------------------------------------------
autosectionlabel_prefix_document = True

# -- numpydoc --------------------------------------------------------------------------
numpydoc_class_members_toctree = False
numpydoc_attributes_as_param_list = False

# x-ref
numpydoc_xref_param_type = True
numpydoc_xref_aliases = {
    # Matplotlib
    "Axes": "matplotlib.axes.Axes",
    "Axes3D": "mpl_toolkits.mplot3d.axes3d.Axes3D",
    "Figure": "matplotlib.figure.Figure",
    # MNE
    "ConductorModel": "mne.bem.ConductorModel",
    "DigMontage": "mne.channels.DigMontage",
    "Epochs": "mne.Epochs",
    "Evoked": "mne.Evoked",
    "Info": "mne.Info",
    "Projection": "mne.Projection",
    "Raw": "mne.io.Raw",
    # MNE-LSL
    "EpochsStream": "mne_lsl.stream.EpochsStream",
    "StreamInfo": "mne_lsl.lsl.StreamInfo",
    "StreamInlet": "mne_lsl.lsl.StreamInlet",
    "StreamOutlet": "mne_lsl.lsl.StreamOutlet",
    # Numpy
    "dtype": "numpy.dtype",
    # Python
    "bool": ":class:`python:bool`",
    "file-like": ":term:`file-like <python:file object>`",
    "path-like": ":term:`path-like`",
    "Path": "pathlib.Path",
    "TextIO": "io.TextIOBase",
}
numpydoc_xref_ignore = {
    "hex",
    "instance",
    "length",
    "n_ch_groups",
    "n_channels",
    "n_epochs",
    "n_picks",
    "n_samples",
    "of",
    "shape",
}

# validation
# https://numpydoc.readthedocs.io/en/latest/validation.html#validation-checks
error_ignores = {
    "GL01",  # docstring should start in the line immediately after the quotes
    "EX01",  # section 'Examples' not found
    "ES01",  # no extended summary found
    "SA01",  # section 'See Also' not found
    "SA04",  # no description in See Also
    "RT02",  # the first line of the Returns section should contain only the type, unless multiple values are being returned  # noqa
}
numpydoc_validate = True
numpydoc_validation_checks = {"all"} | set(error_ignores)
numpydoc_validation_exclude = {  # regex to ignore during docstring check
    r"\.__getitem__",
    r"\.__contains__",
    r"\.__hash__",
    r"\.__mul__",
    r"\.__sub__",
    r"\.__add__",
    r"\.__iter__",
    r"\.__div__",
    r"\.__neg__",
}

# -- sphinxcontrib-bibtex --------------------------------------------------------------
bibtex_bibfiles = ["./references.bib"]

# -- sphinx.ext.linkcode ---------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html


def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
    """Determine the URL corresponding to a Python object.

    Parameters
    ----------
    domain : str
        One of 'py', 'c', 'cpp', 'javascript'.
    info : dict
        With keys "module" and "fullname".

    Returns
    -------
    url : str | None
        The code URL. If None, no link is added.
    """
    if domain != "py":
        return None  # only document python objects

    # retrieve pyobject and file
    try:
        module = import_module(info["module"])
        pyobject = module
        for elt in info["fullname"].split("."):
            pyobject = getattr(pyobject, elt)
        pyobject = inspect.unwrap(pyobject)
        fname = inspect.getsourcefile(pyobject).replace("\\", "/")
        if not Path(fname).exists():
            return None
    except Exception:
        # Either the object could not be loaded or the file was not found.
        # For instance, properties will raise.
        return None

    # retrieve start/stop lines
    source, start_line = inspect.getsourcelines(pyobject)
    lines = f"L{start_line}-L{start_line + len(source) - 1}"

    # create URL
    if "/mne/" in fname:
        # that's an MNE-Python inherited method/function/class
        fname = fname.rsplit("/mne/")[1]
        mne_version = ".".join(mne.__version__.rsplit(".")[:2])
        return f"{gh_url_mne}/blob/maint/{mne_version}/mne/{fname}#{lines}"

    fname = fname.rsplit(f"/{package}/")[1]
    if "dev" in release:
        branch = "main"
    else:
        maint_version = ".".join(release.rsplit(".")[:2])
        branch = f"maint/{maint_version}"
    return f"{gh_url}/blob/{branch}/src/{package}/{fname}#{lines}"


# -- sphinx-gallery --------------------------------------------------------------------
if sys.platform.startswith("win"):
    try:
        subprocess.check_call(["optipng", "--version"])
        compress_images = ("images", "thumbnails")
    except Exception:
        compress_images = ()
    ignore_pattern = r"__init__\.py|00_player_separate_process"
else:
    compress_images = ("images", "thumbnails")
    ignore_pattern = r"__init__\.py"

sphinx_gallery_conf = {
    "backreferences_dir": "generated/backreferences",
    "compress_images": compress_images,
    "doc_module": (f"{package}",),
    "examples_dirs": ["../tutorials", "../examples"],
    "exclude_implicit_doc": {},  # set
    "filename_pattern": r"\d{2}_",
    "gallery_dirs": ["generated/tutorials", "generated/examples"],
    "ignore_pattern": ignore_pattern,
    "line_numbers": False,
    "plot_gallery": "True",  # str, to enable overwrite from CLI without warning
    "reference_url": {f"{package}": None},
    "remove_config_comments": True,
    "show_memory": True,
    "within_subsection_order": FileNameSortKey,
}

# -- sphinx-remove-toctrees ------------------------------------------------------------
remove_from_toctrees = ["generated/api/*"]

# -- linkcheck -------------------------------------------------------------------------
linkcheck_anchors = False  # saves a bit of time
linkcheck_timeout = 15  # some can be quite slow
linkcheck_retries = 3
linkcheck_ignore = []  # will be compiled to regex

# -- sphinx_copybutton -----------------------------------------------------------------
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
