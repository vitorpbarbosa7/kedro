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

"""This module provides a set of classes which underpin the data loading and
saving functionality provided by ``kedro.io``.
"""

import abc
import copy
import logging
import re
import warnings
from collections import namedtuple
from datetime import datetime, timezone
from functools import partial
from glob import iglob
from operator import attrgetter
from pathlib import Path, PurePath, PurePosixPath
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from urllib.parse import urlsplit

from cachetools import Cache, cachedmethod
from cachetools.keys import hashkey

from kedro.utils import load_obj

warnings.simplefilter("default", DeprecationWarning)

VERSION_FORMAT = "%Y-%m-%dT%H.%M.%S.%fZ"
VERSIONED_FLAG_KEY = "versioned"
VERSION_KEY = "version"
HTTP_PROTOCOLS = ("http", "https")
PROTOCOL_DELIMITER = "://"
CLOUD_PROTOCOLS = ("s3", "gcs", "gs", "adl", "abfs")


class DataSetError(Exception):
    """``DataSetError`` raised by ``AbstractDataSet`` implementations
    in case of failure of input/output methods.

    ``AbstractDataSet`` implementations should provide instructive
    information in case of failure.
    """

    pass


class DataSetNotFoundError(DataSetError):
    """``DataSetNotFoundError`` raised by ``DataCatalog`` class in case of
    trying to use a non-existing data set.
    """

    pass


class DataSetAlreadyExistsError(DataSetError):
    """``DataSetAlreadyExistsError`` raised by ``DataCatalog`` class in case
    of trying to add a data set which already exists in the ``DataCatalog``.
    """

    pass


class VersionNotFoundError(DataSetError):
    """``VersionNotFoundError`` raised by ``AbstractVersionedDataSet`` implementations
    in case of no load versions available for the data set.
    """

    pass


class AbstractDataSet(abc.ABC):
    """``AbstractDataSet`` is the base class for all data set implementations.
    All data set implementations should extend this abstract class
    and implement the methods marked as abstract.

    Example:
    ::

        >>> from pathlib import Path, PurePosixPath
        >>> import pandas as pd
        >>> from kedro.io import AbstractDataSet
        >>>
        >>>
        >>> class MyOwnDataSet(AbstractDataSet):
        >>>     def __init__(self, filepath, param1, param2=True):
        >>>         self._filepath = PurePosixPath(filepath)
        >>>         self._param1 = param1
        >>>         self._param2 = param2
        >>>
        >>>     def _load(self) -> pd.DataFrame:
        >>>         return pd.read_csv(self._filepath)
        >>>
        >>>     def _save(self, df: pd.DataFrame) -> None:
        >>>         df.to_csv(str(self._filepath))
        >>>
        >>>     def _exists(self) -> bool:
        >>>         return Path(self._filepath.as_posix()).exists()
        >>>
        >>>     def _describe(self):
        >>>         return dict(param1=self._param1, param2=self._param2)

    Example catalog.yml specification:
    ::

        my_dataset:
            type: <path-to-my-own-dataset>.MyOwnDataSet
            filepath: data/01_raw/my_data.csv
            param1: <param1-value> # param1 is a required argument
            # param2 will be True by default
    """

    @classmethod
    def from_config(
        cls: Type,
        name: str,
        config: Dict[str, Any],
        load_version: str = None,
        save_version: str = None,
    ) -> "AbstractDataSet":
        """Create a data set instance using the configuration provided.

        Args:
            name: Data set name.
            config: Data set config dictionary.
            load_version: Version string to be used for ``load`` operation if
                the data set is versioned. Has no effect on the data set
                if versioning was not enabled.
            save_version: Version string to be used for ``save`` operation if
                the data set is versioned. Has no effect on the data set
                if versioning was not enabled.

        Returns:
            An instance of an ``AbstractDataSet`` subclass.

        Raises:
            DataSetError: When the function fails to create the data set
                from its config.

        """
        try:
            class_obj, config = parse_dataset_definition(
                config, load_version, save_version
            )
        except Exception as ex:
            raise DataSetError(
                "An exception occurred when parsing config "
                "for DataSet `{}`:\n{}".format(name, str(ex))
            )

        try:
            data_set = class_obj(**config)  # type: ignore
        except TypeError as err:
            raise DataSetError(
                "\n{}.\nDataSet '{}' must only contain "
                "arguments valid for the constructor "
                "of `{}.{}`.".format(
                    str(err), name, class_obj.__module__, class_obj.__qualname__
                )
            )
        except Exception as err:
            raise DataSetError(
                "\n{}.\nFailed to instantiate DataSet "
                "'{}' of type `{}.{}`.".format(
                    str(err), name, class_obj.__module__, class_obj.__qualname__
                )
            )
        return data_set

    @property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    def load(self) -> Any:
        """Loads data by delegation to the provided load method.

        Returns:
            Data returned by the provided load method.

        Raises:
            DataSetError: When underlying load method raises error.

        """

        self._logger.debug("Loading %s", str(self))

        try:
            return self._load()
        except DataSetError:
            raise
        except Exception as exc:
            # This exception handling is by design as the composed data sets
            # can throw any type of exception.
            message = "Failed while loading data from data set {}.\n{}".format(
                str(self), str(exc)
            )
            raise DataSetError(message) from exc

    def save(self, data: Any) -> None:
        """Saves data by delegation to the provided save method.

        Args:
            data: the value to be saved by provided save method.

        Raises:
            DataSetError: when underlying save method raises error.

        """

        if data is None:
            raise DataSetError("Saving `None` to a `DataSet` is not allowed")

        try:
            self._logger.debug("Saving %s", str(self))
            self._save(data)
        except DataSetError:
            raise
        except Exception as exc:
            message = "Failed while saving data to data set {}.\n{}".format(
                str(self), str(exc)
            )
            raise DataSetError(message) from exc

    def __str__(self):
        def _to_str(obj, is_root=False):
            """Returns a string representation where
            1. The root level (i.e. the DataSet.__init__ arguments) are
            formatted like DataSet(key=value).
            2. Dictionaries have the keys alphabetically sorted recursively.
            3. None values are not shown.
            """

            fmt = "{}={}" if is_root else "'{}': {}"  # 1

            if isinstance(obj, dict):
                sorted_dict = sorted(obj.items(), key=lambda pair: str(pair[0]))  # 2

                text = ", ".join(
                    fmt.format(key, _to_str(value))  # 2
                    for key, value in sorted_dict
                    if value is not None  # 3
                )

                return text if is_root else "{" + text + "}"  # 1

            # not a dictionary
            return str(obj)

        return "{}({})".format(type(self).__name__, _to_str(self._describe(), True))

    @abc.abstractmethod
    def _load(self) -> Any:
        raise NotImplementedError(
            "`{}` is a subclass of AbstractDataSet and"
            "it must implement the `_load` method".format(self.__class__.__name__)
        )

    @abc.abstractmethod
    def _save(self, data: Any) -> None:
        raise NotImplementedError(
            "`{}` is a subclass of AbstractDataSet and"
            "it must implement the `_save` method".format(self.__class__.__name__)
        )

    @abc.abstractmethod
    def _describe(self) -> Dict[str, Any]:
        raise NotImplementedError(
            "`{}` is a subclass of AbstractDataSet and"
            "it must implement the `_describe` method".format(self.__class__.__name__)
        )

    def exists(self) -> bool:
        """Checks whether a data set's output already exists by calling
        the provided _exists() method.

        Returns:
            Flag indicating whether the output already exists.

        Raises:
            DataSetError: when underlying exists method raises error.

        """
        try:
            self._logger.debug("Checking whether target of %s exists", str(self))
            return self._exists()
        except Exception as exc:
            message = "Failed during exists check for data set {}.\n{}".format(
                str(self), str(exc)
            )
            raise DataSetError(message) from exc

    def _exists(self) -> bool:
        self._logger.warning(
            "`exists()` not implemented for `%s`. Assuming output does not exist.",
            self.__class__.__name__,
        )
        return False

    def release(self) -> None:
        """Release any cached data.

        Raises:
            DataSetError: when underlying release method raises error.

        """
        try:
            self._logger.debug("Releasing %s", str(self))
            self._release()
        except Exception as exc:
            message = "Failed during release for data set {}.\n{}".format(
                str(self), str(exc)
            )
            raise DataSetError(message) from exc

    def _release(self) -> None:
        pass

    def _copy(self, **overwrite_params) -> "AbstractDataSet":
        dataset_copy = copy.deepcopy(self)
        for name, value in overwrite_params.items():
            setattr(dataset_copy, name, value)
        return dataset_copy


def generate_timestamp() -> str:
    """Generate the timestamp to be used by versioning.

    Returns:
        String representation of the current timestamp.

    """
    current_ts = datetime.now(tz=timezone.utc).strftime(VERSION_FORMAT)
    return current_ts[:-4] + current_ts[-1:]  # Don't keep microseconds


class Version(namedtuple("Version", ["load", "save"])):
    """This namedtuple is used to provide load and save versions for versioned
    data sets. If ``Version.load`` is None, then the latest available version
    is loaded. If ``Version.save`` is None, then save version is formatted as
    YYYY-MM-DDThh.mm.ss.sssZ of the current timestamp.
    """

    __slots__ = ()


_CONSISTENCY_WARNING = (
    "Save version `{}` did not match load version `{}` for {}. This is strongly "
    "discouraged due to inconsistencies it may cause between `save` and "
    "`load` operations. Please refrain from setting exact load version for "
    "intermediate data sets where possible to avoid this warning."
)

_DEFAULT_PACKAGES = ["kedro.io.", "kedro.extras.datasets.", ""]


def parse_dataset_definition(
    config: Dict[str, Any], load_version: str = None, save_version: str = None
) -> Tuple[Type[AbstractDataSet], Dict[str, Any]]:
    """Parse and instantiate a dataset class using the configuration provided.

    Args:
        config: Data set config dictionary. It *must* contain the `type` key
            with fully qualified class name.
        load_version: Version string to be used for ``load`` operation if
                the data set is versioned. Has no effect on the data set
                if versioning was not enabled.
        save_version: Version string to be used for ``save`` operation if
            the data set is versioned. Has no effect on the data set
            if versioning was not enabled.

    Raises:
        DataSetError: If the function fails to parse the configuration provided.

    Returns:
        2-tuple: (Dataset class object, configuration dictionary)
    """
    save_version = save_version or generate_timestamp()
    config = copy.deepcopy(config)

    if "type" not in config:
        raise DataSetError("`type` is missing from DataSet catalog configuration")

    class_obj = config.pop("type")
    if isinstance(class_obj, str):
        if len(class_obj.strip(".")) != len(class_obj):
            raise DataSetError(
                "`type` class path does not support relative "
                "paths or paths ending with a dot."
            )

        class_paths = (prefix + class_obj for prefix in _DEFAULT_PACKAGES)

        trials = (_load_obj(class_path) for class_path in class_paths)
        try:
            class_obj = next(obj for obj in trials if obj is not None)
        except StopIteration:
            raise DataSetError("Class `{}` not found.".format(class_obj))

    if not issubclass(class_obj, AbstractDataSet):
        raise DataSetError(
            "DataSet type `{}.{}` is invalid: all data set types must extend "
            "`AbstractDataSet`.".format(class_obj.__module__, class_obj.__qualname__)
        )

    if VERSION_KEY in config:
        # remove "version" key so that it's not passed
        # to the "unversioned" data set constructor
        message = (
            "`%s` attribute removed from data set configuration since it is a "
            "reserved word and cannot be directly specified"
        )
        logging.getLogger(__name__).warning(message, VERSION_KEY)
        del config[VERSION_KEY]
    if config.pop(VERSIONED_FLAG_KEY, False):  # data set is versioned
        config[VERSION_KEY] = Version(load_version, save_version)

    return class_obj, config


def _load_obj(class_path: str) -> Optional[object]:
    mod_path, _, class_name = class_path.rpartition(".")
    try:
        available_classes = load_obj(f"{mod_path}.__all__")
    # ModuleNotFoundError: When `load_obj` can't find `mod_path` (e.g `kedro.io.pandas`)
    #                      this is because we try a combination of all prefixes.
    # AttributeError: When `load_obj` manages to load `mod_path` but it doesn't have an
    #                 `__all__` attribute -- either because it's a custom or a kedro.io dataset
    except (ModuleNotFoundError, AttributeError, ValueError):
        available_classes = None

    try:
        class_obj = load_obj(class_path)
    except (ModuleNotFoundError, ValueError):
        return None
    except AttributeError as error:
        if available_classes and class_name in available_classes:
            raise DataSetError(
                f"{error} Please see the documentation on how to "
                f"install relevant dependencies for {class_path}:\n"
                f"https://kedro.readthedocs.io/en/stable/02_getting_started/"
                f"02_install.html#optional-dependencies"
            )
        return None

    return class_obj


def _local_exists(filepath: str) -> bool:  # SKIP_IF_NO_SPARK
    filepath = Path(filepath)
    return filepath.exists() or any(par.is_file() for par in filepath.parents)


class AbstractVersionedDataSet(AbstractDataSet, abc.ABC):
    """
    ``AbstractVersionedDataSet`` is the base class for all versioned data set
    implementations. All data sets that implement versioning should extend this
    abstract class and implement the methods marked as abstract.

    Example:
    ::

        >>> from pathlib import Path, PurePosixPath
        >>> import pandas as pd
        >>> from kedro.io import AbstractVersionedDataSet
        >>>
        >>>
        >>> class MyOwnDataSet(AbstractVersionedDataSet):
        >>>     def __init__(self, filepath, version, param1, param2=True):
        >>>         super().__init__(PurePosixPath(filepath), version)
        >>>         self._param1 = param1
        >>>         self._param2 = param2
        >>>
        >>>     def _load(self) -> pd.DataFrame:
        >>>         load_path = self._get_load_path()
        >>>         return pd.read_csv(load_path)
        >>>
        >>>     def _save(self, df: pd.DataFrame) -> None:
        >>>         save_path = self._get_save_path()
        >>>         df.to_csv(str(save_path))
        >>>
        >>>     def _exists(self) -> bool:
        >>>         path = self._get_load_path()
        >>>         return Path(path.as_posix()).exists()
        >>>
        >>>     def _describe(self):
        >>>         return dict(version=self._version, param1=self._param1, param2=self._param2)

    Example catalog.yml specification:
    ::

        my_dataset:
            type: <path-to-my-own-dataset>.MyOwnDataSet
            filepath: data/01_raw/my_data.csv
            versioned: true
            param1: <param1-value> # param1 is a required argument
            # param2 will be True by default
    """

    def __init__(
        self,
        filepath: PurePosixPath,
        version: Optional[Version],
        exists_function: Callable[[str], bool] = None,
        glob_function: Callable[[str], List[str]] = None,
    ):
        """Creates a new instance of ``AbstractVersionedDataSet``.

        Args:
            filepath: Filepath in POSIX format to a file.
            version: If specified, should be an instance of
                ``kedro.io.core.Version``. If its ``load`` attribute is
                None, the latest version will be loaded. If its ``save``
                attribute is None, save version will be autogenerated.
            exists_function: Function that is used for determining whether
                a path exists in a filesystem.
            glob_function: Function that is used for finding all paths
                in a filesystem, which match a given pattern.
        """
        self._filepath = filepath
        self._version = version
        self._exists_function = exists_function or _local_exists
        self._glob_function = glob_function or iglob
        # 1 entry for load version, 1 for save version
        self._version_cache = Cache(maxsize=2)

    # 'key' is set to prevent cache key overlapping for load and save:
    # https://cachetools.readthedocs.io/en/stable/#cachetools.cachedmethod
    @cachedmethod(cache=attrgetter("_version_cache"), key=partial(hashkey, "load"))
    def _fetch_latest_load_version(self) -> str:
        # When load version is unpinned, fetch the most recent existing
        # version from the given path.
        pattern = str(self._get_versioned_path("*"))
        version_paths = sorted(self._glob_function(pattern), reverse=True)
        most_recent = next(
            (path for path in version_paths if self._exists_function(path)), None
        )

        if not most_recent:
            raise VersionNotFoundError(f"Did not find any versions for {self}")

        return PurePath(most_recent).parent.name

    # 'key' is set to prevent cache key overlapping for load and save:
    # https://cachetools.readthedocs.io/en/stable/#cachetools.cachedmethod
    @cachedmethod(cache=attrgetter("_version_cache"), key=partial(hashkey, "save"))
    def _fetch_latest_save_version(self) -> str:  # pylint: disable=no-self-use
        """Generate and cache the current save version"""
        return generate_timestamp()

    def resolve_load_version(self) -> Optional[str]:
        """Compute the version the dataset should be loaded with."""
        if not self._version:
            return None
        if self._version.load:
            return self._version.load
        return self._fetch_latest_load_version()

    def _get_load_path(self) -> PurePosixPath:
        if not self._version:
            # When versioning is disabled, load from original filepath
            return self._filepath

        load_version = self.resolve_load_version()
        return self._get_versioned_path(load_version)  # type: ignore

    def resolve_save_version(self) -> Optional[str]:
        """Compute the version the dataset should be saved with."""
        if not self._version:
            return None
        if self._version.save:
            return self._version.save
        return self._fetch_latest_save_version()

    def _get_save_path(self) -> PurePosixPath:
        if not self._version:
            # When versioning is disabled, return original filepath
            return self._filepath

        save_version = self.resolve_save_version()
        versioned_path = self._get_versioned_path(save_version)  # type: ignore

        if self._exists_function(str(versioned_path)):
            raise DataSetError(
                "Save path `{}` for {} must not exist if versioning "
                "is enabled.".format(versioned_path, str(self))
            )

        return versioned_path

    def _get_versioned_path(self, version: str) -> PurePosixPath:
        return self._filepath / version / self._filepath.name

    def load(self) -> Any:
        self.resolve_load_version()  # Make sure last load version is set
        return super().load()

    def save(self, data: Any) -> None:
        self._version_cache.clear()
        save_version = self.resolve_save_version()  # Make sure last save version is set
        super().save(data)

        load_version = self.resolve_load_version()
        if load_version != save_version:
            warnings.warn(
                _CONSISTENCY_WARNING.format(save_version, load_version, str(self))
            )

    def exists(self) -> bool:
        """Checks whether a data set's output already exists by calling
        the provided _exists() method.

        Returns:
            Flag indicating whether the output already exists.

        Raises:
            DataSetError: when underlying exists method raises error.

        """
        self._logger.debug("Checking whether target of %s exists", str(self))
        try:
            return self._exists()
        except VersionNotFoundError:
            return False
        except Exception as exc:  # SKIP_IF_NO_SPARK
            message = "Failed during exists check for data set {}.\n{}".format(
                str(self), str(exc)
            )
            raise DataSetError(message) from exc

    def _release(self) -> None:
        super()._release()
        self._version_cache.clear()


def _parse_filepath(filepath: str) -> Dict[str, str]:
    """Split filepath on protocol and path. Based on `fsspec.utils.infer_storage_options`.

    Args:
        filepath: Either local absolute file path or URL (s3://bucket/file.csv)

    Returns:
        Parsed filepath.
    """
    if (
        re.match(r"^[a-zA-Z]:[\\/]", filepath)
        or re.match(r"^[a-zA-Z0-9]+://", filepath) is None
    ):
        return {"protocol": "file", "path": filepath}

    parsed_path = urlsplit(filepath)
    protocol = parsed_path.scheme or "file"

    if protocol in HTTP_PROTOCOLS:
        return {"protocol": protocol, "path": filepath}

    path = parsed_path.path
    if protocol == "file":
        windows_path = re.match(r"^/([a-zA-Z])[:|]([\\/].*)$", path)
        if windows_path:
            path = "{}:{}".format(*windows_path.groups())

    options = {"protocol": protocol, "path": path}

    if parsed_path.netloc:
        if protocol in CLOUD_PROTOCOLS:
            host_with_port = parsed_path.netloc.rsplit("@", 1)[-1]
            host = host_with_port.rsplit(":", 1)[0]
            options["path"] = host + options["path"]

    return options


def get_protocol_and_path(filepath: str, version: Version = None) -> Tuple[str, str]:
    """Parses filepath on protocol and path.

    Args:
        filepath: raw filepath e.g.: `gcs://bucket/test.json`.
        version: instance of ``kedro.io.core.Version`` or None.

    Returns:
        Protocol and path.

    Raises:
        DataSetError: when protocol is http(s) and version is not None.
        Note: HTTP(s) dataset doesn't support versioning.
    """
    options_dict = _parse_filepath(filepath)
    path = options_dict["path"]
    protocol = options_dict["protocol"]

    if protocol in HTTP_PROTOCOLS:
        if version:
            raise DataSetError(
                "HTTP(s) DataSet doesn't support versioning. "
                "Please remove version flag from the dataset configuration."
            )
        path = path.split(PROTOCOL_DELIMITER, 1)[-1]

    return protocol, path


def get_filepath_str(path: PurePath, protocol: str) -> str:
    """Returns filepath. Returns full filepath (with protocol) if protocol is HTTP(s).

    Args:
        path: filepath without protocol.
        protocol: protocol.

    Returns:
        Filepath string.
    """
    path = path.as_posix()
    if protocol in HTTP_PROTOCOLS:
        path = "".join((protocol, PROTOCOL_DELIMITER, path))
    return path


def validate_on_forbidden_chars(**kwargs):
    """Validate that string values do not include white-spaces or ;"""
    for key, value in kwargs.items():
        if " " in value or ";" in value:
            raise DataSetError(
                "Neither white-space nor semicolon are allowed in `{}`.".format(key)
            )
