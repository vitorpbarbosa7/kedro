from datetime import date
from kedro.config import OmegaConfigLoader
from omegaconf.resolvers import oc

loader = OmegaConfigLoader(
    conf_source="conf",
    base_env="base",        # default, but explicit is nice
    default_run_env="local",# env whose configs override base
    config_patterns={
        # keys here must match what you later access via loader["..."]
        "parameters": ["parameters*", "**/parameters*"],
        "catalog": ["catalog*", "**/catalog*"],
        "credentials": ["credentials*", "**/credentials*"],
    },
    merge_strategy={
        # SOFT merge → deep/recursive merge for these sections
        "parameters": "soft",
        "catalog": "soft",
        # this one stays destructive (replace whole top-level key)
        "credentials": "destructive",
    },
    custom_resolvers={
        "today": lambda: date.today().isoformat(),
        "oc.env": oc.env,
    },
)

params = loader["parameters"]  # merged (base + local) with soft strategy
cat = loader["catalog"]

