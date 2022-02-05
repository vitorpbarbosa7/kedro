# Copyright 2020 QuantumBlack Visual Analytics Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NONINFRINGEMENT. IN NO EVENT WILL THE LICENSOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The QuantumBlack Visual Analytics Limited ("QuantumBlack") name and logo
# (either separately or in combination, "QuantumBlack Trademarks") are
# trademarks of QuantumBlack. The License does not grant you any right or
# license to the QuantumBlack Trademarks. You may not use the QuantumBlack
# Trademarks or any confusingly similar mark as a trademark for your product,
# or use the QuantumBlack Trademarks in any other manner that might cause
# confusion in the marketplace, including but not limited to in advertising,
# on websites, or on software.
#
# See the License for the specific language governing permissions and
# limitations under the License.
"""Behave environment setup commands."""
# pylint: disable=unused-argument

import os
import shutil
import tempfile
import venv
from pathlib import Path
from typing import Set

from features.steps.sh_run import run

_PATHS_TO_REMOVE = set()  # type: Set[Path]

FRESH_VENV_TAG = "fresh_venv"


def call(cmd, env):
    res = run(cmd, env=env)
    if res.returncode:
        print(res.stdout)
        print(res.stderr)
        assert False


def before_all(context):
    """Environment preparation before other cli tests are run.
    Installs (core) kedro by running pip in the top level directory.
    """
    context = _setup_kedro_install_venv(context)


def after_all(context):
    for path in _PATHS_TO_REMOVE:
        # ignore errors when attempting to remove already removed directories
        shutil.rmtree(path, ignore_errors=True)


def before_scenario(context, scenario):
    if FRESH_VENV_TAG in scenario.tags:
        context = _setup_kedro_install_venv(context)

    context.temp_dir = Path(tempfile.mkdtemp()).resolve()
    _PATHS_TO_REMOVE.add(context.temp_dir)


def _setup_context_with_venv(context, venv_dir):
    context.venv_dir = venv_dir
    # note the locations of some useful stuff
    # this is because exe resolution in subprocess doesn't respect a passed env
    if os.name == "posix":
        bin_dir = context.venv_dir / "bin"
        path_sep = ":"
    else:
        bin_dir = context.venv_dir / "Scripts"
        path_sep = ";"
    context.bin_dir = bin_dir
    context.pip = str(bin_dir / "pip")
    context.python = str(bin_dir / "python")
    context.kedro = str(bin_dir / "kedro")
    context.requirements_path = Path("requirements.txt").resolve()

    # clone the environment, remove any condas and venvs and insert our venv
    context.env = os.environ.copy()
    path = context.env["PATH"].split(path_sep)
    path = [p for p in path if not (Path(p).parent / "pyvenv.cfg").is_file()]
    path = [p for p in path if not (Path(p).parent / "conda-meta").is_dir()]
    path = [str(bin_dir)] + path
    context.env["PATH"] = path_sep.join(path)

    # Create an empty pip.conf file and point pip to it
    pip_conf_path = context.venv_dir / "pip.conf"
    pip_conf_path.touch()
    context.env["PIP_CONFIG_FILE"] = str(pip_conf_path)

    return context


def _create_new_venv() -> Path:
    """Create a new venv.

    Returns:
        path to created venv
    """
    # Create venv
    venv_dir = _create_tmp_dir()
    venv.main([str(venv_dir)])
    return venv_dir


def _create_tmp_dir() -> Path:
    """Create a temp directory and add it to _PATHS_TO_REMOVE"""
    tmp_dir = Path(tempfile.mkdtemp()).resolve()
    _PATHS_TO_REMOVE.add(tmp_dir)
    return tmp_dir


def _setup_kedro_install_venv(context):
    kedro_install_venv_dir = _create_new_venv()
    context.kedro_install_venv_dir = kedro_install_venv_dir
    context = _setup_context_with_venv(context, kedro_install_venv_dir)
    call(
        [
            context.python,
            "-m",
            "pip",
            "install",
            "-U",
            "pip>=20.0,<20.2",
            "setuptools>=38.0",
            "wheel",
        ],
        env=context.env,
    )
    install_reqs = (
        Path(
            "kedro/templates/project/{{ cookiecutter.repo_name }}/src/requirements.txt"
        )
        .read_text()
        .splitlines()
    )
    install_reqs = [req for req in install_reqs if "{" not in req]
    install_reqs.append(".[pandas.CSVDataSet]")

    call([context.pip, "install", *install_reqs], env=context.env)
    return context
