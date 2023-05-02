#https://docs.kedro.org/en/stable/kedro_project_setup/session.html
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pathlib import Path

# https://docs.kedro.org/en/stable/kedro.io.DataCatalog.html
# https://docs.kedro.org/en/stable/data/data_catalog.html
from kedro.io.data_catalog import DataCatalog
from kedro.extras.datasets.pandas import CSVDataSet

toy_conf = CSVDataSet(filepath = 'data/01_raw/toy.csv',
                    load_args=None,
                    save_args=None)

# Creating the reference to the dataset with dict
catalog = DataCatalog(data_sets={'toy2':toy_conf})

print('io Code API DataCatalog \n')
toy = catalog.load('toy2')
print(toy.values)
print(dir(catalog))
print('\n List of datasets:')
print(catalog.list())

metadata = bootstrap_project(Path.cwd())

print(f'\nProject metadata : \n {metadata}')

# overriding parameters
parameters = {'x':7}

with KedroSession.create(
    
            package_name = metadata.package_name,
            extra_params=parameters) as session:
    
    context = session.load_context()

    print(f'\nContext: \n {context}')
    print(dir(context))

    # catalog = context.catalog
    # print(f'\nCatalog: \n {catalog}')
    # print(dir(catalog))
    # print(catalog.datasets)

    parameters = context.params

    print(f'\nParameters: \n {parameters}')

    session.run(pipeline_name='pc')

