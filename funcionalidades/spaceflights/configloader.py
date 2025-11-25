from kedro.config import OmegaConfigLoader
loader = OmegaConfigLoader(conf_source="conf")

params = loader["parameters"]
print(params)

