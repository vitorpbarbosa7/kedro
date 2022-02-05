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

"""This file has been deprecated and will be deleted in 0.17.0. Please add additional tests in
`tests.template.test_load_context_framework.py` instead.
"""

import re
import sys
from pathlib import Path

import pytest

import kedro
from kedro.context import KedroContextError, load_context


@pytest.fixture(autouse=True)
def mock_logging_config(mocker):
    # Disable logging.config.dictConfig in KedroContext._setup_logging as
    # it changes logging.config and affects other unit tests
    mocker.patch("logging.config.dictConfig")


class TestLoadContext:
    def test_valid_context(self, fake_repo_path):
        """Test getting project context."""
        result = load_context(str(fake_repo_path))
        assert result.project_name == "Test Project"
        assert result.project_version == kedro.__version__
        assert str(fake_repo_path.resolve() / "src") in sys.path

    def test_valid_context_with_env(self, mocker, monkeypatch, fake_repo_path):
        """Test getting project context when Kedro config environment is
        specified in the environment variable.
        """
        mocker.patch("kedro.config.config.ConfigLoader.get")
        monkeypatch.setenv("KEDRO_ENV", "my_fake_env")
        result = load_context(str(fake_repo_path))
        assert result.env == "my_fake_env"

    def test_invalid_path(self, tmp_path):
        """Test for loading context from an invalid path. """
        other_path = tmp_path / "other"
        other_path.mkdir()
        pattern = r"Could not find '\.kedro\.yml'"
        with pytest.raises(KedroContextError, match=pattern):
            load_context(str(other_path))

    def test_kedro_yml_invalid_format(self, fake_repo_path):
        """Test for loading context from an invalid path. """
        kedro_yml_path = fake_repo_path / ".kedro.yml"
        kedro_yml_path.write_text("!!")  # Invalid YAML
        pattern = r"Failed to parse '\.kedro\.yml' file"
        with pytest.raises(KedroContextError, match=pattern):
            load_context(str(fake_repo_path))

    def test_kedro_yml_has_no_context_path(self, fake_repo_path):
        """Test for loading context from an invalid path. """
        kedro_yml_path = fake_repo_path / ".kedro.yml"
        kedro_yml_path.write_text("fake_key: fake_value\nsource_dir: src\n")
        pattern = r"'\.kedro\.yml' doesn't have a required `context_path` field"
        with pytest.raises(KedroContextError, match=pattern):
            load_context(str(fake_repo_path))

    @pytest.mark.parametrize("source_dir", ["src", "./src", "./src/"])
    def test_kedro_yml_valid_source_dir(
        self, mocker, monkeypatch, fake_repo_path, source_dir
    ):
        """Test for loading context from an valid source dir. """
        monkeypatch.delenv(
            "PYTHONPATH"
        )  # test we are also adding source_dir to PYTHONPATH as well

        kedro_yml_path = fake_repo_path / ".kedro.yml"
        kedro_yml_path.write_text(
            f"context_path: fake_package.run.ProjectContext\nsource_dir: {source_dir}\n"
        )

        result = load_context(str(fake_repo_path))
        assert result.project_name == "Test Project"
        assert result.project_version == kedro.__version__
        assert str(fake_repo_path.resolve() / source_dir) in sys.path

    @pytest.mark.parametrize(
        "source_dir", ["../", "../src/", "./src/../..", "/User/user/root_project"]
    )
    def test_kedro_yml_invalid_source_dir_pattern(self, fake_repo_path, source_dir):
        """Test for invalid pattern for source_dir that is not relative to the project path.
        """
        kedro_yml_path = fake_repo_path / ".kedro.yml"
        kedro_yml_path.write_text(
            f"context_path: fake_package.run.ProjectContext\nsource_dir: {source_dir}\n"
        )
        source_path = (fake_repo_path / Path(source_dir).expanduser()).resolve()

        pattern = re.escape(
            f"Source path '{source_path}' has to be relative to your project root "
            f"'{fake_repo_path.resolve()}'"
        )
        with pytest.raises(KedroContextError, match=pattern):
            load_context(str(fake_repo_path))

    def test_source_path_does_not_exist(self, fake_repo_path):
        """Test for a valid source_dir pattern, but it does not exist.
        """
        kedro_yml_path = fake_repo_path / ".kedro.yml"
        source_dir = "non_existent"
        kedro_yml_path.write_text(
            f"context_path: fake_package.run.ProjectContext\nsource_dir: {source_dir}\n"
        )
        non_existent_path = (fake_repo_path / source_dir).expanduser().resolve()

        pattern = re.escape(f"Source path '{non_existent_path}' cannot be found")
        with pytest.raises(KedroContextError, match=pattern):
            load_context(str(fake_repo_path))

    def test_kedro_yml_missing_source_dir(self, fake_repo_path):
        """If source dir is missing (it is by default), `src` is used to import package
           due to backward compatibility.
        """
        kedro_yml_path = fake_repo_path / ".kedro.yml"
        kedro_yml_path.write_text("context_path: fake_package.run.ProjectContext\n")

        result = load_context(str(fake_repo_path))
        assert result.project_name == "Test Project"
        assert result.project_version == kedro.__version__
        assert str(fake_repo_path.resolve() / "src") in sys.path
