#https://docs.kedro.org/en/stable/kedro_project_setup/session.html
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pathlib import Path

metadata = bootstrap_project(Path.cwd())

print(f'\nProject metadata : \n {metadata}')

parameters = {'x':7}

class KedroFacade:
    def __init__(self, pipeline:str, extra_params:dict):
        self._pipeline = pipeline
        self._extra_params = extra_params

    def  run(self):
        with KedroSession.create(
            package_name = metadata.package_name,
            #overwrite original parameters
            extra_params=self._extra_params) as session:
            context = session.load_context()

        parameters = context.params

        print(f'\nParameters: \n {parameters}')

        session.run(pipeline_name=self._pipeline)

        return None
    
    #TODO implement modulartion for kedrosession and content, for run to call only the session.run()
