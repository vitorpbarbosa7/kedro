# src/spaceflights/hooks.py

import logging
from typing import Any, Dict

from kedro.framework.hooks import hook_impl
from kedro.pipeline.node import Node

logger = logging.getLogger(__name__)

import logging
import time
from typing import Any, Dict
import pandas as pd

from kedro.framework.hooks import hook_impl
from kedro.pipeline.node import Node
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline


class DebugHooks:
    """Simple debug hooks for node execution."""

    @hook_impl
    def before_node_run(
        self,
        node: Node,
        inputs: Dict[str, Any],
    ) -> None:
        logger.info(
            "[before_node_run] #################### node=%s, inputs=%s",
            node.name,
            list(inputs.keys()),
        )

    @hook_impl
    def after_node_run(
        self,
        node: Node,
        outputs: Dict[str, Any],
    ) -> None:
        logger.info(
            "[after_node_run] node=%s, outputs=%s",
            node.name,
            list(outputs.keys()),
        )



class MonitoringHooks:
    """Collects execution metrics for each node and pipeline."""

    def __init__(self):
        self._node_start_times = {}
        self._pipeline_start = None

    # -------------------------------------------------------------------------
    # NODE-LEVEL HOOKS
    # -------------------------------------------------------------------------

    @hook_impl
    def before_node_run(self, node: Node, inputs: Dict[str, Any]):
        self._node_start_times[node.name] = time.time()

        # Estimate input sizes if possible
        sizes = {}
        for name, val in inputs.items():
            if isinstance(val, pd.DataFrame):
                sizes[name] = f"{len(val):,} rows x {len(val.columns)} cols"
            else:
                sizes[name] = type(val).__name__

        logger.info(f"▶️  Node '{node.name}' starting. Inputs: {sizes}")
        breakpoint()

    @hook_impl
    def after_node_run(self, node: Node, outputs: Dict[str, Any]):
        duration = time.time() - self._node_start_times.pop(node.name, time.time())

        # Estimate output sizes
        sizes = {}
        for name, val in outputs.items():
            if isinstance(val, pd.DataFrame):
                sizes[name] = f"{len(val):,} rows x {len(val.columns)} cols"
            else:
                sizes[name] = type(val).__name__

        logger.info(
            f"✅ Node '{node.name}' finished in {duration:.2f}s. Outputs: {sizes}"
        )

    # -------------------------------------------------------------------------
    # PIPELINE-LEVEL HOOKS
    # -------------------------------------------------------------------------

    @hook_impl
    def before_pipeline_run(self, run_params: Dict[str, Any], pipeline: Pipeline, catalog: DataCatalog):
        self._pipeline_start = time.time()
        logger.info(f"🚀 Starting pipeline '{run_params['pipeline_name']}' (env={run_params['env']})")

    @hook_impl
    def after_pipeline_run(
        self,
        run_params: Dict[str, Any],
        run_result: Dict[str, Any],
        pipeline: Pipeline,
        catalog: DataCatalog,
    ):
        duration = time.time() - self._pipeline_start
        logger.info(f"🏁 Pipeline '{run_params['pipeline_name']}' finished in {duration:.2f}s")