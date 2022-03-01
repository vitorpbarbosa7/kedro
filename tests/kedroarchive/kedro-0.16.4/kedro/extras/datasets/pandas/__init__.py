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

"""``AbstractDataSet`` implementations that produce pandas DataFrames."""

__all__ = [
    "CSVDataSet",
    "ExcelDataSet",
    "FeatherDataSet",
    "GBQTableDataSet",
    "ExcelDataSet",
    "AppendableExcelDataSet",
    "HDFDataSet",
    "JSONDataSet",
    "ParquetDataSet",
    "SQLQueryDataSet",
    "SQLTableDataSet",
]

from contextlib import suppress

with suppress(ImportError):
    from .csv_dataset import CSVDataSet  # NOQA
with suppress(ImportError):
    from .excel_dataset import ExcelDataSet  # NOQA
with suppress(ImportError):
    from .appendable_excel_dataset import AppendableExcelDataSet  # NOQA
with suppress(ImportError):
    from .feather_dataset import FeatherDataSet  # NOQA
with suppress(ImportError):
    from .gbq_dataset import GBQTableDataSet  # NOQA
with suppress(ImportError):
    from .hdf_dataset import HDFDataSet  # NOQA
with suppress(ImportError):
    from .json_dataset import JSONDataSet  # NOQA
with suppress(ImportError):
    from .parquet_dataset import ParquetDataSet  # NOQA
with suppress(ImportError):
    from .sql_dataset import SQLQueryDataSet, SQLTableDataSet  # NOQA
