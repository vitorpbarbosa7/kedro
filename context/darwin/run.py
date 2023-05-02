from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pathlib import Path

print(Path.cwd())

bootstrap_project(Path.cwd())
with KedroSession.create() as session:
    session.run()

