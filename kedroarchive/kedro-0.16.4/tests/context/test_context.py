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

import configparser
import json
import re
import sys
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from time import sleep
from typing import Any, Dict

import pandas as pd
import pytest
import yaml
from pandas.util.testing import assert_frame_equal

from kedro import __version__ as kedro_version
from kedro.config import MissingConfigException
from kedro.context import KedroContext, KedroContextError, validate_source_path
from kedro.context.context import (
    _convert_paths_to_absolute_posix,
    _is_relative_path,
    _validate_layers_for_transcoding,
)
from kedro.extras.datasets.pandas import CSVDataSet
from kedro.io.core import Version, generate_timestamp
from kedro.pipeline import Pipeline, node
from kedro.runner import ParallelRunner, SequentialRunner


def _get_local_logging_config():
    return {
        "version": 1,
        "formatters": {
            "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "kedro": {"level": "INFO", "handlers": ["console"], "propagate": False}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "logs/info.log",
        },
    }


def _write_yaml(filepath: Path, config: Dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


def _write_json(filepath: Path, config: Dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(config)
    filepath.write_text(json_str)


def _write_dummy_ini(filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    config["prod"] = {"url": "postgresql://user:pass@url_prod/db"}
    config["staging"] = {"url": "postgresql://user:pass@url_staging/db"}
    with filepath.open("wt") as configfile:  # save
        config.write(configfile)


@pytest.fixture
def base_config(tmp_path):
    cars_filepath = (tmp_path / "cars.csv").as_posix()
    trains_filepath = (tmp_path / "trains.csv").as_posix()

    return {
        "trains": {"type": "pandas.CSVDataSet", "filepath": trains_filepath},
        "cars": {
            "type": "pandas.CSVDataSet",
            "filepath": cars_filepath,
            "save_args": {"index": True},
        },
    }


@pytest.fixture
def local_config(tmp_path):
    cars_filepath = (tmp_path / "cars.csv").as_posix()
    boats_filepath = (tmp_path / "boats.csv").as_posix()
    # use one dataset with a relative filepath
    horses_filepath = "horses.csv"
    return {
        "cars": {
            "type": "pandas.CSVDataSet",
            "filepath": cars_filepath,
            "save_args": {"index": False},
            "versioned": True,
        },
        "boats": {
            "type": "pandas.CSVDataSet",
            "filepath": boats_filepath,
            "versioned": True,
            "layer": "raw",
        },
        "horses": {
            "type": "pandas.CSVDataSet",
            "filepath": horses_filepath,
            "versioned": True,
        },
    }


@pytest.fixture(params=[None])
def env(request):
    return request.param


@pytest.fixture
def config_dir(tmp_path, base_config, local_config, env):
    env = "local" if env is None else env
    proj_catalog = tmp_path / "conf" / "base" / "catalog.yml"
    env_catalog = tmp_path / "conf" / str(env) / "catalog.yml"
    env_credentials = tmp_path / "conf" / str(env) / "credentials.yml"
    env_logging = tmp_path / "conf" / str(env) / "logging.yml"
    parameters = tmp_path / "conf" / "base" / "parameters.json"
    db_config_path = tmp_path / "conf" / "base" / "db.ini"
    project_parameters = {"param1": 1, "param2": 2, "param3": {"param4": 3}}
    _write_yaml(proj_catalog, base_config)
    _write_yaml(env_catalog, local_config)
    _write_yaml(env_credentials, local_config)
    _write_yaml(env_logging, _get_local_logging_config())
    _write_json(parameters, project_parameters)
    _write_dummy_ini(db_config_path)


@pytest.fixture
def dummy_dataframe():
    return pd.DataFrame({"col1": [1, 2], "col2": [4, 5], "col3": [5, 6]})


def identity(input1: str):
    return input1  # pragma: no cover


def bad_node(x):
    raise ValueError("Oh no!")


bad_pipeline_middle = Pipeline(
    [
        node(identity, "cars", "boats", name="node1", tags=["tag1"]),
        node(identity, "boats", "trains", name="node2"),
        node(bad_node, "trains", "ships", name="nodes3"),
        node(identity, "ships", "planes", name="node4"),
    ],
    tags="bad_pipeline",
)

expected_message_middle = (
    "There are 2 nodes that have not run.\n"
    "You can resume the pipeline run by adding the following "
    "argument to your previous command:\n"
    '  --from-nodes "nodes3"'
)


bad_pipeline_head = Pipeline(
    [
        node(bad_node, "cars", "boats", name="node1", tags=["tag1"]),
        node(identity, "boats", "trains", name="node2"),
        node(identity, "trains", "ships", name="nodes3"),
        node(identity, "ships", "planes", name="node4"),
    ],
    tags="bad_pipeline",
)

expected_message_head = (
    "There are 4 nodes that have not run.\n"
    "You can resume the pipeline run by adding the following "
    "argument to your previous command:\n"
)


class DummyContext(KedroContext):
    project_name = "bob"
    project_version = kedro_version
    package_name = "bob"

    def _get_pipelines(self) -> Dict[str, Pipeline]:
        pipeline = Pipeline(
            [
                node(identity, "cars", "boats", name="node1", tags=["tag1"]),
                node(identity, "boats", "trains", name="node2"),
                node(identity, "trains", "ships", name="node3"),
                node(identity, "ships", "planes", name="node4"),
            ],
            tags="pipeline",
        )
        return {"__default__": pipeline}


class DummyContextWithPipelinePropertyOnly(KedroContext):
    """
    We need this for testing the backward compatibility.
    """

    project_name = "bob_old"
    project_version = kedro_version
    package_name = "bob_old"

    @property
    def pipeline(self) -> Pipeline:
        return Pipeline(
            [
                node(identity, "cars", "boats", name="node1", tags=["tag1"]),
                node(identity, "boats", "trains", name="node2"),
                node(identity, "trains", "ships", name="node3"),
                node(identity, "ships", "planes", name="node4"),
            ],
            tags="pipeline",
        )


@pytest.fixture(params=[None])
def extra_params(request):
    return request.param


@pytest.fixture
def dummy_context(tmp_path, mocker, env, extra_params):
    # Disable logging.config.dictConfig in KedroContext._setup_logging as
    # it changes logging.config and affects other unit tests
    mocker.patch("logging.config.dictConfig")
    return DummyContext(str(tmp_path), env=env, extra_params=extra_params)


@pytest.mark.usefixtures("config_dir")
class TestKedroContext:
    def test_attributes(self, tmp_path, dummy_context):
        assert dummy_context.project_name == "bob"
        assert dummy_context.project_version == kedro_version
        assert isinstance(dummy_context.project_path, Path)
        assert dummy_context.project_path == tmp_path.resolve()

    def test_get_catalog_always_using_absolute_path(self, dummy_context):
        conf_catalog = dummy_context.config_loader.get("catalog*")

        # even though the raw configuration uses relative path
        assert conf_catalog["horses"]["filepath"] == "horses.csv"

        # the catalog and its dataset should be loaded using absolute path
        # based on the project path
        catalog = dummy_context._get_catalog()
        ds_path = catalog._data_sets["horses"]._filepath
        assert PurePath(ds_path.as_posix()).is_absolute()
        assert (
            ds_path.as_posix()
            == (dummy_context._project_path / "horses.csv").as_posix()
        )

    def test_get_catalog_validates_layers(self, dummy_context, mocker):
        mock_validate = mocker.patch(
            "kedro.framework.context.context._validate_layers_for_transcoding"
        )

        catalog = dummy_context._get_catalog()

        mock_validate.assert_called_once_with(catalog)

    def test_catalog(self, dummy_context, dummy_dataframe):
        assert dummy_context.catalog.layers == {"raw": {"boats"}}
        dummy_context.catalog.save("cars", dummy_dataframe)
        reloaded_df = dummy_context.catalog.load("cars")
        assert_frame_equal(reloaded_df, dummy_dataframe)

    def test_io(self, dummy_context, dummy_dataframe):
        dummy_context.io.save("cars", dummy_dataframe)
        reloaded_df = dummy_context.io.load("cars")
        assert_frame_equal(reloaded_df, dummy_dataframe)

    @pytest.mark.parametrize(
        "extra_params",
        [None, {}, {"foo": "bar", "baz": [1, 2], "qux": None}],
        indirect=True,
    )
    def test_params(self, dummy_context, extra_params):
        extra_params = extra_params or {}
        expected = {"param1": 1, "param2": 2, "param3": {"param4": 3}, **extra_params}
        assert dummy_context.params == expected

    @pytest.mark.parametrize(
        "param,expected",
        [("params:param3", {"param4": 3}), ("params:param3.param4", 3)],
    )
    def test_nested_params(self, param, expected, dummy_context):
        param = dummy_context.catalog.load(param)
        assert param == expected

    @pytest.mark.parametrize(
        "extra_params",
        [None, {}, {"foo": "bar", "baz": [1, 2], "qux": None}],
        indirect=True,
    )
    def test_params_missing(self, dummy_context, mocker, extra_params):
        mock_config_loader = mocker.patch.object(DummyContext, "config_loader")
        mock_config_loader.get.side_effect = MissingConfigException("nope")
        extra_params = extra_params or {}

        pattern = "Parameters not found in your Kedro project config"
        with pytest.warns(UserWarning, match=pattern):
            actual = dummy_context.params
        assert actual == extra_params

    def test_config_loader(self, dummy_context):
        params = dummy_context.config_loader.get("parameters*")
        db_conf = dummy_context.config_loader.get("db*")
        catalog = dummy_context.config_loader.get("catalog*")

        assert params["param1"] == 1
        assert db_conf["prod"]["url"] == "postgresql://user:pass@url_prod/db"

        assert catalog["trains"]["type"] == "pandas.CSVDataSet"
        assert catalog["cars"]["type"] == "pandas.CSVDataSet"
        assert catalog["boats"]["type"] == "pandas.CSVDataSet"
        assert not catalog["cars"]["save_args"]["index"]

    def test_default_env(self, dummy_context):
        assert dummy_context.env == "local"

    @pytest.mark.parametrize(
        "invalid_version", ["0.13.0", "10.0", "101.1", "100.0", "-0"]
    )
    def test_invalid_version(self, tmp_path, mocker, invalid_version):
        # Disable logging.config.dictConfig in KedroContext._setup_logging as
        # it changes logging.config and affects other unit tests
        mocker.patch("logging.config.dictConfig")

        class _DummyContext(KedroContext):
            project_name = "bob"
            package_name = "bob"
            project_version = invalid_version

            def _get_pipelines(self) -> Dict[str, Pipeline]:
                return {"__default__": Pipeline([])}  # pragma: no cover

        pattern = (
            r"Your Kedro project version {} does not match "
            r"Kedro package version {} you are running. ".format(
                invalid_version, kedro_version
            )
        )
        with pytest.raises(KedroContextError, match=pattern):
            _DummyContext(str(tmp_path))

    @pytest.mark.parametrize("env", ["custom_env"], indirect=True)
    def test_custom_env(self, dummy_context, env):
        assert dummy_context.env == env

    def test_missing_parameters(self, tmp_path, mocker):
        parameters = tmp_path / "conf" / "base" / "parameters.json"
        parameters.unlink()

        # Disable logging.config.dictConfig in KedroContext._setup_logging as
        # it changes logging.config and affects other unit tests
        mocker.patch("logging.config.dictConfig")

        pattern = "Parameters not found in your Kedro project config."
        with pytest.warns(UserWarning, match=re.escape(pattern)):
            DummyContext(  # pylint: disable=expression-not-assigned
                str(tmp_path)
            ).catalog

    def test_missing_credentials(self, tmp_path, mocker):
        env_credentials = tmp_path / "conf" / "local" / "credentials.yml"
        env_credentials.unlink()

        # Disable logging.config.dictConfig in KedroContext._setup_logging as
        # it changes logging.config and affects other unit tests
        mocker.patch("logging.config.dictConfig")

        pattern = "Credentials not found in your Kedro project config."
        with pytest.warns(UserWarning, match=re.escape(pattern)):
            DummyContext(  # pylint: disable=expression-not-assigned
                str(tmp_path)
            ).catalog

    def test_pipeline(self, dummy_context):
        assert dummy_context.pipeline.nodes[0].inputs == ["cars"]
        assert dummy_context.pipeline.nodes[0].outputs == ["boats"]
        assert dummy_context.pipeline.nodes[1].inputs == ["boats"]
        assert dummy_context.pipeline.nodes[1].outputs == ["trains"]

    def test_pipelines(self, dummy_context):
        assert len(dummy_context.pipelines) == 1
        assert len(dummy_context.pipelines["__default__"].nodes) == 4

    def test_setup_logging_using_absolute_path(self, tmp_path, mocker):
        mocked_dict_config = mocker.patch("logging.config.dictConfig")
        dummy_context = DummyContext(str(tmp_path))
        called_args = mocked_dict_config.call_args[0][0]
        assert (
            called_args["info_file_handler"]["filename"]
            == (dummy_context._project_path / "logs" / "info.log").as_posix()
        )


@pytest.mark.usefixtures("config_dir")
class TestKedroContextRun:
    def test_run_output(self, dummy_context, dummy_dataframe):
        dummy_context.catalog.save("cars", dummy_dataframe)
        outputs = dummy_context.run()
        pd.testing.assert_frame_equal(outputs["planes"], dummy_dataframe)

    def test_run_no_output(self, dummy_context, dummy_dataframe):
        dummy_context.catalog.save("cars", dummy_dataframe)
        outputs = dummy_context.run(node_names=["node1"])
        assert not outputs

    def test_default_run(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run()

        log_msgs = [record.getMessage() for record in caplog.records]
        log_names = [record.name for record in caplog.records]

        assert "kedro.runner.sequential_runner" in log_names
        assert "Pipeline execution completed successfully." in log_msgs

    def test_sequential_run_arg(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(runner=SequentialRunner())

        log_msgs = [record.getMessage() for record in caplog.records]
        log_names = [record.name for record in caplog.records]
        assert "kedro.runner.sequential_runner" in log_names
        assert "Pipeline execution completed successfully." in log_msgs

    @pytest.mark.skipif(
        sys.platform.startswith("win"), reason="Due to bug in parallel runner"
    )
    def test_parallel_run_arg(self, dummy_context, dummy_dataframe, caplog, mocker):
        mocker.patch(
            "kedro.framework.context.context.load_context", return_value=dummy_context
        )
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(runner=ParallelRunner())

        log_msgs = [record.getMessage() for record in caplog.records]
        log_names = [record.name for record in caplog.records]
        assert "kedro.runner.parallel_runner" in log_names
        assert "Pipeline execution completed successfully." in log_msgs

    def test_run_with_node_names(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(node_names=["node1"])

        log_msgs = [record.getMessage() for record in caplog.records]
        assert "Running node: node1: identity([cars]) -> [boats]" in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs
        assert "Running node: node2: identity([boats]) -> [trains]" not in log_msgs

    def test_run_with_node_names_and_tags(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(node_names=["node1"], tags=["tag1", "pipeline"])

        log_msgs = [record.getMessage() for record in caplog.records]
        assert "Running node: node1: identity([cars]) -> [boats]" in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs
        assert "Running node: node2: identity([boats]) -> [trains]" not in log_msgs

    def test_run_with_tags(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(tags=["tag1"])
        log_msgs = [record.getMessage() for record in caplog.records]

        assert "Completed 1 out of 1 tasks" in log_msgs
        assert "Running node: node1: identity([cars]) -> [boats]" in log_msgs
        assert "Running node: node2: identity([boats]) -> [trains]" not in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs

    def test_run_with_wrong_tags(self, dummy_context, dummy_dataframe):
        dummy_context.catalog.save("cars", dummy_dataframe)
        pattern = r"Pipeline contains no nodes with tags: \['non\-existent'\]"
        with pytest.raises(KedroContextError, match=pattern):
            dummy_context.run(tags=["non-existent"])

    def test_run_from_nodes(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(from_nodes=["node1"])

        log_msgs = [record.getMessage() for record in caplog.records]
        assert "Completed 4 out of 4 tasks" in log_msgs
        assert "Running node: node1: identity([cars]) -> [boats]" in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs

    def test_run_to_nodes(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(to_nodes=["node2"])

        log_msgs = [record.getMessage() for record in caplog.records]
        assert "Completed 2 out of 2 tasks" in log_msgs
        assert "Running node: node1: identity([cars]) -> [boats]" in log_msgs
        assert "Running node: node2: identity([boats]) -> [trains]" in log_msgs
        assert "Running node: node3: identity([trains]) -> [ships]" not in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs

    def test_run_with_node_range(self, dummy_context, dummy_dataframe, caplog):
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(from_nodes=["node1"], to_nodes=["node3"])

        log_msgs = [record.getMessage() for record in caplog.records]
        assert "Completed 3 out of 3 tasks" in log_msgs
        assert "Running node: node1: identity([cars]) -> [boats]" in log_msgs
        assert "Running node: node2: identity([boats]) -> [trains]" in log_msgs
        assert "Running node: node3: identity([trains]) -> [ships]" in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs

    def test_run_with_invalid_node_range(self, dummy_context, dummy_dataframe):
        dummy_context.catalog.save("cars", dummy_dataframe)
        pattern = "Pipeline contains no nodes"

        with pytest.raises(KedroContextError, match=pattern):
            dummy_context.run(from_nodes=["node3"], to_nodes=["node1"])

    def test_run_from_inputs(self, dummy_context, dummy_dataframe, caplog):
        for dataset in ("cars", "trains", "boats"):
            dummy_context.catalog.save(dataset, dummy_dataframe)
        dummy_context.run(from_inputs=["trains"])

        log_msgs = [record.getMessage() for record in caplog.records]
        assert "Completed 2 out of 2 tasks" in log_msgs
        assert "Running node: node3: identity([trains]) -> [ships]" in log_msgs
        assert "Running node: node4: identity([ships]) -> [planes]" in log_msgs
        assert "Pipeline execution completed successfully." in log_msgs

    def test_run_load_versions(self, tmp_path, dummy_context, dummy_dataframe, mocker):
        class DummyContext(KedroContext):
            project_name = "bob"
            package_name = "bob"
            project_version = kedro_version

            def _get_pipelines(self) -> Dict[str, Pipeline]:
                return {"__default__": Pipeline([node(identity, "cars", "boats")])}

        mocker.patch("logging.config.dictConfig")
        dummy_context = DummyContext(str(tmp_path))
        filepath = (dummy_context.project_path / "cars.csv").as_posix()

        old_save_version = generate_timestamp()
        old_df = pd.DataFrame({"col1": [0, 0], "col2": [0, 0], "col3": [0, 0]})
        old_csv_data_set = CSVDataSet(
            filepath=filepath,
            save_args={"sep": ","},
            version=Version(None, old_save_version),
        )
        old_csv_data_set.save(old_df)

        sleep(0.5)
        new_save_version = generate_timestamp()
        new_csv_data_set = CSVDataSet(
            filepath=filepath,
            save_args={"sep": ","},
            version=Version(None, new_save_version),
        )
        new_csv_data_set.save(dummy_dataframe)

        load_versions = {"cars": old_save_version}
        dummy_context.run(load_versions=load_versions)
        assert not dummy_context.catalog.load("boats").equals(dummy_dataframe)
        assert dummy_context.catalog.load("boats").equals(old_df)

    def test_run_with_empty_pipeline(self, tmp_path, mocker):
        class DummyContext(KedroContext):
            project_name = "bob"
            package_name = "bob"
            project_version = kedro_version

            def _get_pipelines(self) -> Dict[str, Pipeline]:
                return {"__default__": Pipeline([])}

        mocker.patch("logging.config.dictConfig")
        dummy_context = DummyContext(str(tmp_path))
        assert dummy_context.project_name == "bob"
        assert dummy_context.project_version == kedro_version
        pattern = "Pipeline contains no nodes"
        with pytest.raises(KedroContextError, match=pattern):
            dummy_context.run()

    @pytest.mark.parametrize(
        "context_pipeline,expected_message",
        [
            (bad_pipeline_middle, expected_message_middle),
            (bad_pipeline_head, expected_message_head),
        ],  # pylint: disable=too-many-arguments
    )
    def test_run_failure_prompts_resume_command(
        self,
        mocker,
        tmp_path,
        dummy_dataframe,
        caplog,
        context_pipeline,
        expected_message,
    ):
        class BadContext(KedroContext):
            project_name = "fred"
            package_name = "fred"
            project_version = kedro_version

            def _get_pipelines(self) -> Dict[str, Pipeline]:
                return {"__default__": context_pipeline}

        mocker.patch("logging.config.dictConfig")

        bad_context = BadContext(str(tmp_path))
        bad_context.catalog.save("cars", dummy_dataframe)
        with pytest.raises(ValueError, match="Oh no"):
            bad_context.run()

        actual_messages = [
            record.getMessage()
            for record in caplog.records
            if record.levelname == "WARNING"
        ]

        assert expected_message in actual_messages

    def test_missing_pipeline_name(self, dummy_context, dummy_dataframe):
        dummy_context.catalog.save("cars", dummy_dataframe)

        with pytest.raises(KedroContextError, match="Failed to find the pipeline"):
            dummy_context.run(pipeline_name="invalid-name")

    def test_without_get_pipeline_deprecated(
        self, dummy_dataframe, mocker, tmp_path, env
    ):
        """
        The old way of providing a `pipeline` context property is deprecated,
        but still works, yielding a warning message.
        """
        mocker.patch("logging.config.dictConfig")
        dummy_context = DummyContextWithPipelinePropertyOnly(str(tmp_path), env=env)
        dummy_context.catalog.save("cars", dummy_dataframe)

        msg = "You are using the deprecated pipeline construction mechanism"
        with pytest.warns(DeprecationWarning, match=msg):
            outputs = dummy_context.run()

        pd.testing.assert_frame_equal(outputs["planes"], dummy_dataframe)

    def test_without_get_pipeline_error(self, dummy_dataframe, mocker, tmp_path, env):
        """
        The old way of providing a `pipeline` context property is deprecated,
        but still works, yielding a warning message.
        If you try to run a sub-pipeline by name - it's an error.
        """

        mocker.patch("logging.config.dictConfig")
        dummy_context = DummyContextWithPipelinePropertyOnly(str(tmp_path), env=env)
        dummy_context.catalog.save("cars", dummy_dataframe)

        error_msg = "The project is not fully migrated to use multiple pipelines."

        with pytest.raises(KedroContextError, match=error_msg):
            dummy_context.run(pipeline_name="missing-pipeline")

    @pytest.mark.parametrize(
        "extra_params",
        [None, {}, {"foo": "bar", "baz": [1, 2], "qux": None}],
        indirect=True,
    )
    def test_run_with_extra_params(
        self, mocker, dummy_context, dummy_dataframe, extra_params
    ):
        mocker.patch("logging.config.dictConfig")
        mock_journal = mocker.patch("kedro.framework.context.context.Journal")
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run()

        assert mock_journal.call_args[0][0]["extra_params"] == extra_params

    def test_run_with_save_version_as_run_id(
        self, mocker, tmp_path, dummy_dataframe, caplog
    ):
        """Test that the default behaviour, with run_id set to None,
        creates a journal record with the run_id the same as save_version.
        """
        mocker.patch("logging.config.dictConfig")
        save_version = "2020-01-01T00.00.00.000Z"
        mocked_get_save_version = mocker.patch.object(
            DummyContext, "_get_save_version", return_value=save_version
        )

        dummy_context = DummyContext(str(tmp_path))
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run(load_versions={"boats": save_version})

        mocked_get_save_version.assert_called_once_with()
        log_msg = next(
            record.getMessage()
            for record in caplog.records
            if record.name == "kedro.journal"
        )
        assert json.loads(log_msg)["run_id"] == save_version

    def test_run_with_custom_run_id(self, mocker, tmp_path, dummy_dataframe, caplog):
        mocker.patch("logging.config.dictConfig")
        run_id = "001"
        mocked_get_run_id = mocker.patch.object(
            DummyContext, "_get_run_id", return_value=run_id
        )

        dummy_context = DummyContext(str(tmp_path))
        dummy_context.catalog.save("cars", dummy_dataframe)
        dummy_context.run()

        assert (
            mocked_get_run_id.call_count == 3
        )  # once during run, and twice for each `.catalog`
        log_msg = next(
            record.getMessage()
            for record in caplog.records
            if record.name == "kedro.journal"
        )
        assert json.loads(log_msg)["run_id"] == run_id

    @pytest.mark.parametrize(
        "ctx_project_name",
        ["project_name", "Project name ", "_Project--name-", "--Project-_\n ~-namE__"],
    )
    def test_default_package_name(self, tmp_path, mocker, ctx_project_name):
        """Test default package name derived by ProjectContext"""
        mocker.patch("logging.config.dictConfig")

        expected_package_name = "project_name"

        class DummyContextNoPkgName(KedroContext):
            project_name = ctx_project_name
            project_version = kedro_version

            def _get_pipelines(self):  # pragma: no cover
                return {"__default__": Pipeline([])}

        dummy_context = DummyContextNoPkgName(tmp_path)
        assert dummy_context.package_name == expected_package_name


@pytest.mark.parametrize(
    "path_string,expected",
    [
        # remote paths shouldn't be relative paths
        ("s3://", False),
        ("gcp://path/to/file.json", False),
        # windows absolute path shouldn't relative paths
        ("C:\\path\\to\\file.json", False),
        ("C:", False),
        ("C:/Windows/", False),
        # posix absolute path shouldn't be relative paths
        ("/tmp/logs/info.log", False),
        ("/usr/share", False),
        # test relative paths
        ("data/01_raw/data.json", True),
        ("logs/info.log", True),
        ("logs\\error.txt", True),
        ("data", True),
    ],
)
def test_is_relative_path(path_string: str, expected: bool):
    assert _is_relative_path(path_string) == expected


def test_convert_paths_raises_error_on_relative_project_path():
    path = Path("relative/path")
    with pytest.raises(ValueError) as excinfo:
        _convert_paths_to_absolute_posix(project_path=path, conf_dictionary={})

    assert (
        str(excinfo.value) == f"project_path must be an absolute path. Received: {path}"
    )


@pytest.mark.parametrize(
    "project_path,input_conf,expected",
    [
        (
            PurePosixPath("/tmp"),
            {"handler": {"filename": "logs/info.log"}},
            {"handler": {"filename": "/tmp/logs/info.log"}},
        ),
        (
            PurePosixPath("/User/kedro"),
            {"my_dataset": {"filepath": "data/01_raw/dataset.json"}},
            {"my_dataset": {"filepath": "/User/kedro/data/01_raw/dataset.json"}},
        ),
        (
            PureWindowsPath("C:\\kedro"),
            {"my_dataset": {"path": "data/01_raw/dataset.json"}},
            {"my_dataset": {"path": "C:/kedro/data/01_raw/dataset.json"}},
        ),
        # test: the function shouldn't modify paths for key not associated with filepath
        (
            PurePosixPath("/User/kedro"),
            {"my_dataset": {"fileurl": "relative/url"}},
            {"my_dataset": {"fileurl": "relative/url"}},
        ),
    ],
)
def test_convert_paths_to_absolute_posix_for_all_known_filepath_keys(
    project_path: Path, input_conf: Dict[str, Any], expected: Dict[str, Any]
):
    assert _convert_paths_to_absolute_posix(project_path, input_conf) == expected


@pytest.mark.parametrize(
    "project_path,input_conf,expected",
    [
        (
            PurePosixPath("/tmp"),
            {"handler": {"filename": "/usr/local/logs/info.log"}},
            {"handler": {"filename": "/usr/local/logs/info.log"}},
        ),
        (
            PurePosixPath("/User/kedro"),
            {"my_dataset": {"filepath": "s3://data/01_raw/dataset.json"}},
            {"my_dataset": {"filepath": "s3://data/01_raw/dataset.json"}},
        ),
    ],
)
def test_convert_paths_to_absolute_posix_not_changing_non_relative_path(
    project_path: Path, input_conf: Dict[str, Any], expected: Dict[str, Any]
):
    assert _convert_paths_to_absolute_posix(project_path, input_conf) == expected


@pytest.mark.parametrize(
    "project_path,input_conf,expected",
    [
        (
            PureWindowsPath("D:\\kedro"),
            {"my_dataset": {"path": r"C:\data\01_raw\dataset.json"}},
            {"my_dataset": {"path": "C:/data/01_raw/dataset.json"}},
        )
    ],
)
def test_convert_paths_to_absolute_posix_converts_full_windows_path_to_posix(
    project_path: Path, input_conf: Dict[str, Any], expected: Dict[str, Any]
):
    assert _convert_paths_to_absolute_posix(project_path, input_conf) == expected


@pytest.mark.parametrize(
    "layers",
    [
        {"raw": {"A"}, "interm": {"B", "C"}},
        {"raw": {"A"}, "interm": {"B@2", "B@1"}},
        {"raw": {"C@1"}, "interm": {"A", "B@1", "B@2", "B@3"}},
    ],
)
def test_validate_layers(layers, mocker):
    mock_catalog = mocker.MagicMock()
    mock_catalog.layers = layers

    _validate_layers_for_transcoding(mock_catalog)  # it shouldn't raise any error


@pytest.mark.parametrize(
    "layers,conflicting_datasets",
    [
        ({"raw": {"A", "B@1"}, "interm": {"B@2"}}, ["B@2"]),
        ({"raw": {"A"}, "interm": {"B@1", "B@2"}, "prm": {"B@3"}}, ["B@3"]),
        (
            {
                "raw": {"A@1"},
                "interm": {"B@1", "B@2"},
                "prm": {"B@3", "B@4"},
                "other": {"A@2"},
            },
            ["A@2", "B@3", "B@4"],
        ),
    ],
)
def test_validate_layers_error(layers, conflicting_datasets, mocker):
    mock_catalog = mocker.MagicMock()
    mock_catalog.layers = layers
    error_str = ", ".join(conflicting_datasets)

    pattern = f"Transcoded datasets should have the same layer. Mismatch found for: {error_str}"
    with pytest.raises(ValueError, match=re.escape(pattern)):
        _validate_layers_for_transcoding(mock_catalog)


class TestValidateSourcePath:
    @pytest.mark.parametrize(
        "source_dir", [".", "src", "./src", "src/nested", "src/nested/nested"]
    )
    def test_valid_source_path(self, tmp_path, source_dir):
        source_path = (tmp_path / source_dir).resolve()
        source_path.mkdir(parents=True, exist_ok=True)
        validate_source_path(source_path, tmp_path.resolve())

    @pytest.mark.parametrize("source_dir", ["..", "src/../..", "~"])
    def test_invalid_source_path(self, tmp_path, source_dir):
        source_dir = Path(source_dir).expanduser()
        source_path = (tmp_path / source_dir).resolve()
        source_path.mkdir(parents=True, exist_ok=True)

        pattern = re.escape(
            f"Source path '{source_path}' has to be relative to your project root "
            f"'{tmp_path.resolve()}'"
        )
        with pytest.raises(KedroContextError, match=pattern):
            validate_source_path(source_path, tmp_path.resolve())

    def test_non_existent_source_path(self, tmp_path):
        source_path = (tmp_path / "non_existent").resolve()

        pattern = re.escape(f"Source path '{source_path}' cannot be found.")
        with pytest.raises(KedroContextError, match=pattern):
            validate_source_path(source_path, tmp_path.resolve())
