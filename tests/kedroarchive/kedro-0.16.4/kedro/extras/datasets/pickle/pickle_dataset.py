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

"""``PickleDataSet`` loads/saves data from/to a Pickle file using an underlying
filesystem (e.g.: local, S3, GCS). The underlying functionality is supported by
the ``pickle`` and ``joblib`` libraries, so it supports all allowed options for
loading and saving pickle files.
"""
import pickle
from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any, Dict

import fsspec

from kedro.io.core import (
    AbstractVersionedDataSet,
    DataSetError,
    Version,
    get_filepath_str,
    get_protocol_and_path,
)

try:
    import joblib
except ImportError:  # pragma: no cover
    joblib = None


class PickleDataSet(AbstractVersionedDataSet):
    """``PickleDataSet`` loads/saves data from/to a Pickle file using an underlying
    filesystem (e.g.: local, S3, GCS). The underlying functionality is supported by
    the ``pickle`` and ``joblib`` libraries, so it supports all allowed options for
    loading and saving pickle files.

    Example:
    ::

        >>> from kedro.extras.datasets.pickle import PickleDataSet
        >>> import pandas as pd
        >>>
        >>> data = pd.DataFrame({'col1': [1, 2], 'col2': [4, 5],
        >>>                      'col3': [5, 6]})
        >>>
        >>> # data_set = PickleDataSet(filepath="gcs://bucket/test.pkl")
        >>> data_set = PickleDataSet(filepath="test.pkl", backend="pickle")
        >>> data_set.save(data)
        >>> reloaded = data_set.load()
        >>> assert data.equals(reloaded)

    """

    DEFAULT_LOAD_ARGS = {}  # type: Dict[str, Any]
    DEFAULT_SAVE_ARGS = {}  # type: Dict[str, Any]
    BACKENDS = {"pickle": pickle, "joblib": joblib}

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        filepath: str,
        backend: str = "pickle",
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
        version: Version = None,
        credentials: Dict[str, Any] = None,
        fs_args: Dict[str, Any] = None,
    ) -> None:
        """Creates a new instance of ``PickleDataSet`` pointing to a concrete Pickle
        file on a specific filesystem. ``PickleDataSet`` supports two backends to
        serialize/deserialize objects: `pickle` and `joblib`.

        Args:
            filepath: Filepath in POSIX format to a Pickle file prefixed with a protocol like
                `s3://`. If prefix is not provided, `file` protocol (local filesystem) will be used.
                The prefix should be any protocol supported by ``fsspec``.
                Note: `http(s)` doesn't support versioning.
            backend: Backend to use, must be one of ['pickle', 'joblib']. Defaults to 'pickle'.
            load_args: Pickle options for loading pickle files.
                Here you can find all available arguments for different backends:
                pickle.load: https://docs.python.org/3/library/pickle.html#pickle.load
                joblib.load: https://joblib.readthedocs.io/en/latest/generated/joblib.load.html
                All defaults are preserved.
            save_args: Pickle options for saving pickle files.
                Here you can find all available arguments for different backends:
                pickle.dump: https://docs.python.org/3/library/pickle.html#pickle.dump
                joblib.dump: https://joblib.readthedocs.io/en/latest/generated/joblib.dump.html
                All defaults are preserved.
            version: If specified, should be an instance of
                ``kedro.io.core.Version``. If its ``load`` attribute is
                None, the latest version will be loaded. If its ``save``
                attribute is None, save version will be autogenerated.
            credentials: Credentials required to get access to the underlying filesystem.
                E.g. for ``GCSFileSystem`` it should look like `{"token": None}`.
            fs_args: Extra arguments to pass into underlying filesystem class constructor
                (e.g. `{"project": "my-project"}` for ``GCSFileSystem``), as well as
                to pass to the filesystem's `open` method through nested keys
                `open_args_load` and `open_args_save`.
                Here you can find all available arguments for `open`:
                https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.open
                All defaults are preserved, except `mode`, which is set to `wb` when saving.

        Raises:
            ValueError: If ``backend`` is not one of ['pickle', 'joblib'].
            ImportError: If ``backend`` library could not be imported.
        """
        if backend not in self.BACKENDS:
            raise ValueError(
                "'backend' should be one of {}, got '{}'.".format(
                    list(self.BACKENDS.keys()), backend
                )
            )

        if not self.BACKENDS[backend]:
            raise ImportError(
                "Selected backend '{}' could not be "
                "imported. Make sure it is installed.".format(backend)
            )

        _fs_args = deepcopy(fs_args) or {}
        _fs_open_args_load = _fs_args.pop("open_args_load", {})
        _fs_open_args_save = _fs_args.pop("open_args_save", {})
        _credentials = deepcopy(credentials) or {}

        protocol, path = get_protocol_and_path(filepath, version)

        self._protocol = protocol
        self._fs = fsspec.filesystem(self._protocol, **_credentials, **_fs_args)

        super().__init__(
            filepath=PurePosixPath(path),
            version=version,
            exists_function=self._fs.exists,
            glob_function=self._fs.glob,
        )

        self._backend = backend

        # Handle default load and save arguments
        self._load_args = deepcopy(self.DEFAULT_LOAD_ARGS)
        if load_args is not None:
            self._load_args.update(load_args)
        self._save_args = deepcopy(self.DEFAULT_SAVE_ARGS)
        if save_args is not None:
            self._save_args.update(save_args)

        _fs_open_args_save.setdefault("mode", "wb")
        self._fs_open_args_load = _fs_open_args_load
        self._fs_open_args_save = _fs_open_args_save

    def _describe(self) -> Dict[str, Any]:
        return dict(
            filepath=self._filepath,
            backend=self._backend,
            protocol=self._protocol,
            load_args=self._load_args,
            save_args=self._save_args,
            version=self._version,
        )

    def _load(self) -> Any:
        load_path = get_filepath_str(self._get_load_path(), self._protocol)

        with self._fs.open(load_path, **self._fs_open_args_load) as fs_file:
            return self.BACKENDS[self._backend].load(
                fs_file, **self._load_args
            )  # nosec

    def _save(self, data: Any) -> None:
        save_path = get_filepath_str(self._get_save_path(), self._protocol)

        with self._fs.open(save_path, **self._fs_open_args_save) as fs_file:
            try:
                self.BACKENDS[self._backend].dump(data, fs_file, **self._save_args)
            except Exception as err:
                raise DataSetError(
                    "{} was not serialized due to: {}".format(
                        str(data.__class__), str(err)
                    )
                )

        self._invalidate_cache()

    def _exists(self) -> bool:
        try:
            load_path = get_filepath_str(self._get_load_path(), self._protocol)
        except DataSetError:
            return False

        return self._fs.exists(load_path)

    def _release(self) -> None:
        super()._release()
        self._invalidate_cache()

    def _invalidate_cache(self) -> None:
        """Invalidate underlying filesystem caches."""
        filepath = get_filepath_str(self._filepath, self._protocol)
        self._fs.invalidate_cache(filepath)
