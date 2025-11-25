from datetime import date
from kedro.config import OmegaConfigLoader
from omegaconf.resolvers import oc

loader = OmegaConfigLoader(
    conf_source="conf",
    custom_resolvers={
        "today": lambda: date.today().isoformat(),
        "oc.env": oc.env
    }
)

