from pathlib import Path

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.utils import find_kedro_project


def main() -> None:
    # Descobre a raiz do projeto (onde está o pyproject.toml com [tool.kedro])
    current_dir = Path(__file__).resolve().parent
    project_root = find_kedro_project(current_dir)
    print(project_root)

    # Inicializa metadados do projeto (define PACKAGE_NAME etc.)
    metadata = bootstrap_project(project_root)
    print(metadata)

    # Cria a sessão usando o env "dev"
    with KedroSession.create(project_path=project_root, env="dev") as session:
        # Carrega o contexto
        context = session.load_context()

        # Só para debug: mostra env e parâmetros
        print(f"=== ENV ATIVO: {context.env} ===")
        print("=== PARAMETERS (context.params) ===")
        for k, v in context.params.items():
            print(f"{k}: {v}")
        print()

        # Roda apenas o pipeline data_processing
        session.run(pipeline_name="data_processing")


if __name__ == "__main__":
    main()

