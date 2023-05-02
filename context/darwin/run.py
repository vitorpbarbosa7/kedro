from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pathlib import Path

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

    catalog = context.catalog
    parameters = context.params

    print(f'\nCatalog: \n {catalog}')
    print(dir(catalog))

    print(f'\nParameters: \n {parameters}')

    session.run(pipeline_name='pc')

