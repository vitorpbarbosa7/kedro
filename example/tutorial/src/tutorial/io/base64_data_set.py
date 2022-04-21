from kedro.io.core import AbstractDataSet, DataSetError

from base64 import b64encode

class Base64DataSet(AbstractDataSet):
    def __init__(self, filepath):
        self.__filepath = filepath

    def _save(self, binary_data):
        with open(str(self.__filepath), 'wb') as f:
            f.write(b64encode(binary_data))

    def _load(self):
        raise DataSetError('Write Only DataSet')

    def _describe(self):
        return dict(filepath=self.__filepath)