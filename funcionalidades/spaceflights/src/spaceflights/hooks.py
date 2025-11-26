# src/spaceflights/hooks.py

import logging
from typing import Any, Dict

from kedro.framework.hooks import hook_impl
from kedro.pipeline.node import Node

logger = logging.getLogger(__name__)


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

