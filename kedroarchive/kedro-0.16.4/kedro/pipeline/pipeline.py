# Copyright 2020 QuantumBlack Visual Analytics Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NONINFRINGEMENT. IN NO EVENT WILL THE LICENSOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The QuantumBlack Visual Analytics Limited ("QuantumBlack") name and logo
# (either separately or in combination, "QuantumBlack Trademarks") are
# trademarks of QuantumBlack. The License does not grant you any right or
# license to the QuantumBlack Trademarks. You may not use the QuantumBlack
# Trademarks or any confusingly similar mark as a trademark for your product,
# or use the QuantumBlack Trademarks in any other manner that might cause
# confusion in the marketplace, including but not limited to in advertising,
# on websites, or on software.
#
# See the License for the specific language governing permissions and
# limitations under the License.
"""A ``Pipeline`` is a collection of ``Node`` objects which can be executed as
a Directed Acyclic Graph, sequentially or in parallel. The ``Pipeline`` class
offers quick access to input dependencies,
produced outputs and execution order.
"""
import copy
import json
from collections import Counter, defaultdict
from itertools import chain
from typing import Callable, Dict, Iterable, List, Set, Tuple, Union

from toposort import CircularDependencyError as ToposortCircleError
from toposort import toposort

import kedro
from kedro.pipeline.node import Node, _to_list

TRANSCODING_SEPARATOR = "@"


def _transcode_split(element: str) -> Tuple[str, str]:
    """Split the name by the transcoding separator.
    If the transcoding part is missing, empty string will be put in.

    Returns:
        Node input/output name before the transcoding separator, if present.
    Raises:
        ValueError: Raised if more than one transcoding separator
        is present in the name.
    """
    split_name = element.split(TRANSCODING_SEPARATOR)

    if len(split_name) > 2:
        raise ValueError(
            "Expected maximum 1 transcoding separator, found {} instead: '{}'.".format(
                len(split_name) - 1, element
            )
        )
    if len(split_name) == 1:
        split_name.append("")

    return tuple(split_name)  # type: ignore


def _strip_transcoding(element: str) -> str:
    """Strip out the transcoding separator and anything that follows.

    Returns:
        Node input/output name before the transcoding separator, if present.
    Raises:
        ValueError: Raised if more than one transcoding separator
        is present in the name.
    """
    return _transcode_split(element)[0]


class OutputNotUniqueError(Exception):
    """Raised when two or more nodes that are part of the same pipeline
    produce outputs with the same name.
    """

    pass


class ConfirmNotUniqueError(Exception):
    """Raised when two or more nodes that are part of the same pipeline
    attempt to confirm the same dataset.
    """

    pass


class Pipeline:  # pylint: disable=too-many-public-methods
    """A ``Pipeline`` defined as a collection of ``Node`` objects. This class
    treats nodes as part of a graph representation and provides inputs,
    outputs and execution order.
    """

    def __init__(
        self,
        nodes: Iterable[Union[Node, "Pipeline"]],
        *,
        tags: Union[str, Iterable[str]] = None,
    ):
        """Initialise ``Pipeline`` with a list of ``Node`` instances.

        Args:
            nodes: The iterable of nodes the ``Pipeline`` will be made of. If you
                provide pipelines among the list of nodes, those pipelines will
                be expanded and all their nodes will become part of this
                new pipeline.
            tags: Optional set of tags to be applied to all the pipeline nodes.

        Raises:
            ValueError:
                When an empty list of nodes is provided, or when not all
                nodes have unique names.
            CircularDependencyError:
                When visiting all the nodes is not
                possible due to the existence of a circular dependency.
            OutputNotUniqueError:
                When multiple ``Node`` instances produce the same output.
            ConfirmNotUniqueError:
                When multiple ``Node`` instances attempt to confirm the same
                dataset.
        Example:
        ::

            >>> from kedro.pipeline import Pipeline
            >>> from kedro.pipeline import node
            >>>
            >>> # In the following scenario first_ds and second_ds
            >>> # are data sets provided by io. Pipeline will pass these
            >>> # data sets to first_node function and provides the result
            >>> # to the second_node as input.
            >>>
            >>> def first_node(first_ds, second_ds):
            >>>     return dict(third_ds=first_ds+second_ds)
            >>>
            >>> def second_node(third_ds):
            >>>     return third_ds
            >>>
            >>> pipeline = Pipeline([
            >>>     node(first_node, ['first_ds', 'second_ds'], ['third_ds']),
            >>>     node(second_node, dict(third_ds='third_ds'), 'fourth_ds')])
            >>>
            >>> pipeline.describe()
            >>>

        """
        if nodes is None:
            raise ValueError(
                "`nodes` argument of `Pipeline` is None. It must be an "
                "iterable of nodes and/or pipelines instead."
            )
        nodes = list(nodes)  # in case it's a generator
        _validate_duplicate_nodes(nodes)

        nodes = list(
            chain.from_iterable(
                [[n] if isinstance(n, Node) else n.nodes for n in nodes]
            )
        )
        _validate_transcoded_inputs_outputs(nodes)
        _tags = set(_to_list(tags))

        nodes = [n.tag(_tags) for n in nodes]

        self._nodes_by_name = {node.name: node for node in nodes}
        _validate_unique_outputs(nodes)
        _validate_unique_confirms(nodes)

        # input -> nodes with input
        self._nodes_by_input = defaultdict(set)  # type: Dict[str, Set[Node]]
        for node in nodes:
            for input_ in node.inputs:
                self._nodes_by_input[_strip_transcoding(input_)].add(node)

        # output -> node with output
        self._nodes_by_output = {}  # type: Dict[str, Node]
        for node in nodes:
            for output in node.outputs:
                self._nodes_by_output[_strip_transcoding(output)] = node

        self._nodes = nodes
        self._topo_sorted_nodes = _topologically_sorted(self.node_dependencies)

    def __repr__(self):  # pragma: no cover
        """Pipeline ([node1, ..., node10 ...], name='pipeline_name')"""
        max_nodes_to_display = 10

        nodes_reprs = [repr(node) for node in self.nodes[:max_nodes_to_display]]
        if len(self.nodes) > max_nodes_to_display:
            nodes_reprs.append("...")
        nodes_reprs_str = (
            "[\n{}\n]".format(",\n".join(nodes_reprs)) if nodes_reprs else "[]"
        )
        constructor_repr = "({})".format(nodes_reprs_str)
        return "{}{}".format(self.__class__.__name__, constructor_repr)

    def __add__(self, other):
        if not isinstance(other, Pipeline):
            return NotImplemented
        return Pipeline(set(self.nodes + other.nodes))

    def __sub__(self, other):
        if not isinstance(other, Pipeline):
            return NotImplemented
        return Pipeline(set(self.nodes) - set(other.nodes))

    def __and__(self, other):
        if not isinstance(other, Pipeline):
            return NotImplemented
        return Pipeline(set(self.nodes) & set(other.nodes))

    def __or__(self, other):
        if not isinstance(other, Pipeline):
            return NotImplemented
        return Pipeline(set(self.nodes + other.nodes))

    def all_inputs(self) -> Set[str]:
        """All inputs for all nodes in the pipeline.

        Returns:
            All node input names as a Set.

        """
        return set.union(set(), *[node.inputs for node in self.nodes])

    def all_outputs(self) -> Set[str]:
        """All outputs of all nodes in the pipeline.

        Returns:
            All node outputs.

        """
        return set.union(set(), *[node.outputs for node in self.nodes])

    def _remove_intermediates(self, datasets: Set[str]) -> Set[str]:
        intermediate = {_strip_transcoding(i) for i in self.all_inputs()} & {
            _strip_transcoding(o) for o in self.all_outputs()
        }
        return {d for d in datasets if _strip_transcoding(d) not in intermediate}

    def inputs(self) -> Set[str]:
        """The names of free inputs that must be provided at runtime so that
        the pipeline is runnable. Does not include intermediate inputs which
        are produced and consumed by the inner pipeline nodes. Resolves
        transcoded names where necessary.

        Returns:
            The set of free input names needed by the pipeline.

        """
        return self._remove_intermediates(self.all_inputs())

    def outputs(self) -> Set[str]:
        """The names of outputs produced when the whole pipeline is run.
        Does not include intermediate outputs that are consumed by
        other pipeline nodes. Resolves transcoded names where necessary.

        Returns:
            The set of final pipeline outputs.

        """
        return self._remove_intermediates(self.all_outputs())

    def data_sets(self) -> Set[str]:
        """The names of all data sets used by the ``Pipeline``,
        including inputs and outputs.

        Returns:
            The set of all pipeline data sets.

        """
        return self.all_outputs() | self.all_inputs()

    def _transcode_compatible_names(self):
        return {_strip_transcoding(ds) for ds in self.data_sets()}

    def describe(self, names_only: bool = True) -> str:
        """Obtain the order of execution and expected free input variables in
        a loggable pre-formatted string. The order of nodes matches the order
        of execution given by the topological sort.

        Args:
            names_only: The flag to describe names_only pipeline with just
                node names.

        Example:
        ::

            >>> pipeline = Pipeline([ ... ])
            >>>
            >>> logger = logging.getLogger(__name__)
            >>>
            >>> logger.info(pipeline.describe())

        After invocation the following will be printed as an info level log
        statement:
        ::

            #### Pipeline execution order ####
            Inputs: C, D

            func1([C]) -> [A]
            func2([D]) -> [B]
            func3([A, D]) -> [E]

            Outputs: B, E
            ##################################

        Returns:
            The pipeline description as a formatted string.

        """

        def set_to_string(set_of_strings):
            """Convert set to a string but return 'None' in case of an empty
            set.
            """
            return ", ".join(sorted(set_of_strings)) if set_of_strings else "None"

        nodes_as_string = "\n".join(
            node.name if names_only else str(node) for node in self.nodes
        )

        str_representation = (
            "#### Pipeline execution order ####\n"
            "Inputs: {0}\n\n"
            "{1}\n\n"
            "Outputs: {2}\n"
            "##################################"
        )

        return str_representation.format(
            set_to_string(self.inputs()), nodes_as_string, set_to_string(self.outputs())
        )

    @property
    def node_dependencies(self) -> Dict[Node, Set[Node]]:
        """All dependencies of nodes where the first Node has a direct dependency on
        the second Node.

        Returns:
            Dictionary where keys are nodes and values are sets made up of
            their parent nodes. Independent nodes have this as empty sets.
        """
        dependencies = {
            node: set() for node in self._nodes
        }  # type: Dict[Node, Set[Node]]
        for parent in self._nodes:
            for output in parent.outputs:
                for child in self._nodes_by_input[_strip_transcoding(output)]:
                    dependencies[child].add(parent)

        return dependencies

    @property
    def nodes(self) -> List[Node]:
        """Return a list of the pipeline nodes in topological order, i.e. if
        node A needs to be run before node B, it will appear earlier in the
        list.

        Returns:
            The list of all pipeline nodes in topological order.

        """
        return list(chain.from_iterable(self._topo_sorted_nodes))

    @property
    def grouped_nodes(self) -> List[Set[Node]]:
        """Return a list of the pipeline nodes in topologically ordered groups,
        i.e. if node A needs to be run before node B, it will appear in an
        earlier group.

        Returns:
            The pipeline nodes in topologically ordered groups.

        """
        return copy.copy(self._topo_sorted_nodes)

    def only_nodes(self, *node_names: str) -> "Pipeline":
        """Create a new ``Pipeline`` which will contain only the specified
        nodes by name.

        Args:
            node_names: One or more node names. The returned ``Pipeline``
                will only contain these nodes.

        Raises:
            ValueError: When some invalid node name is given.

        Returns:
            A new ``Pipeline``, containing only ``nodes``.

        """
        unregistered_nodes = set(node_names) - set(self._nodes_by_name.keys())
        if unregistered_nodes:
            raise ValueError(
                "Pipeline does not contain nodes named {}.".format(
                    list(unregistered_nodes)
                )
            )

        nodes = [self._nodes_by_name[name] for name in node_names]
        return Pipeline(nodes)

    def only_nodes_with_namespace(self, node_namespace: str) -> "Pipeline":
        """Create a new ``Pipeline`` which will contain only the specified
        nodes by namespace.

        Args:
            node_namespace: One node namespace.

        Raises:
            ValueError: When pipeline contains no pipeline with the specified namespace.

        Returns:
            A new ``Pipeline`` with nodes starting with a specified namespace.

        """
        nodes = [
            n
            for n in self.nodes
            if n.namespace and n.namespace.startswith(node_namespace)
        ]
        if not nodes:
            raise ValueError(
                "Pipeline does not contain nodes with namespace(s) {}.".format(
                    list(node_namespace)
                )
            )
        return Pipeline(nodes)

    def _get_nodes_with_inputs_transcode_compatible(
        self, datasets: Set[str]
    ) -> Set[Node]:
        """Retrieves nodes that use the given `datasets` as inputs.
        If provided a name, but no format, for a transcoded dataset, it
        includes all nodes that use inputs with that name, otherwise it
        matches to the fully-qualified name only (i.e. name@format).

        Raises:
            ValueError: if any of the given datasets do not exist in the
                ``Pipeline`` object

        Returns:
            Set of ``Nodes`` that use the given datasets as inputs.
        """
        missing = sorted(
            datasets - self.data_sets() - self._transcode_compatible_names()
        )
        if missing:
            raise ValueError(
                "Pipeline does not contain data_sets named {}".format(missing)
            )

        relevant_nodes = set()
        for input_ in datasets:
            if _strip_transcoding(input_) == input_:
                relevant_nodes.update(self._nodes_by_input[_strip_transcoding(input_)])
            else:
                for node_ in self._nodes_by_input[_strip_transcoding(input_)]:
                    if input_ in node_.inputs:
                        relevant_nodes.add(node_)
        return relevant_nodes

    def _get_nodes_with_outputs_transcode_compatible(
        self, datasets: Set[str]
    ) -> Set[Node]:
        """Retrieves nodes that output to the given `datasets`.
        If provided a name, but no format, for a transcoded dataset, it
        includes the node that outputs to that name, otherwise it matches
        to the fully-qualified name only (i.e. name@format).

        Raises:
            ValueError: if any of the given datasets do not exist in the
                ``Pipeline`` object

        Returns:
            Set of ``Nodes`` that output to the given datasets.
        """
        missing = sorted(
            datasets - self.data_sets() - self._transcode_compatible_names()
        )
        if missing:
            raise ValueError(
                "Pipeline does not contain data_sets named {}".format(missing)
            )

        relevant_nodes = set()
        for output in datasets:
            if _strip_transcoding(output) in self._nodes_by_output:
                node_with_output = self._nodes_by_output[_strip_transcoding(output)]
                if (
                    _strip_transcoding(output) == output
                    or output in node_with_output.outputs
                ):
                    relevant_nodes.add(node_with_output)

        return relevant_nodes

    def only_nodes_with_inputs(self, *inputs: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes which depend
        directly on the provided inputs.
        If provided a name, but no format, for a transcoded input, it
        includes all the nodes that use inputs with that name, otherwise it
        matches to the fully-qualified name only (i.e. name@format).

        Args:
            inputs: A list of inputs which should be used as a starting
                point of the new ``Pipeline``.

        Raises:
            ValueError: Raised when any of the given inputs do not exist in the
                ``Pipeline`` object.

        Returns:
            A new ``Pipeline`` object, containing a subset of the
                nodes of the current one such that only nodes depending
                directly on the provided inputs are being copied.

        """
        starting = set(inputs)
        nodes = self._get_nodes_with_inputs_transcode_compatible(starting)

        return Pipeline(nodes)

    def from_inputs(self, *inputs: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes which depend
        directly or transitively on the provided inputs.
        If provided a name, but no format, for a transcoded input, it
        includes all the nodes that use inputs with that name, otherwise it
        matches to the fully-qualified name only (i.e. name@format).

        Args:
            inputs: A list of inputs which should be used as a starting point
                of the new ``Pipeline``

        Raises:
            ValueError: Raised when any of the given inputs do not exist in the
                ``Pipeline`` object.

        Returns:
            A new ``Pipeline`` object, containing a subset of the
                nodes of the current one such that only nodes depending
                directly or transitively on the provided inputs are being
                copied.

        """
        starting = set(inputs)
        result = set()  # type: Set[Node]
        next_nodes = self._get_nodes_with_inputs_transcode_compatible(starting)

        while next_nodes:
            result |= next_nodes
            outputs = set(chain.from_iterable(node.outputs for node in next_nodes))
            starting = outputs

            next_nodes = set(
                chain.from_iterable(
                    self._nodes_by_input[_strip_transcoding(input_)]
                    for input_ in starting
                )
            )

        return Pipeline(result)

    def only_nodes_with_outputs(self, *outputs: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes which are directly
        required to produce the provided outputs.
        If provided a name, but no format, for a transcoded dataset, it
        includes all the nodes that output to that name, otherwise it matches
        to the fully-qualified name only (i.e. name@format).

        Args:
            outputs: A list of outputs which should be the final outputs
                of the new ``Pipeline``.

        Raises:
            ValueError: Raised when any of the given outputs do not exist in the
                ``Pipeline`` object.

        Returns:
            A new ``Pipeline`` object, containing a subset of the nodes of the
            current one such that only nodes which are directly required to
            produce the provided outputs are being copied.
        """
        starting = set(outputs)
        nodes = self._get_nodes_with_outputs_transcode_compatible(starting)

        return Pipeline(nodes)

    def to_outputs(self, *outputs: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes which are directly
        or transitively required to produce the provided outputs.
        If provided a name, but no format, for a transcoded dataset, it
        includes all the nodes that output to that name, otherwise it matches
        to the fully-qualified name only (i.e. name@format).

        Args:
            outputs: A list of outputs which should be the final outputs of
                the new ``Pipeline``.

        Raises:
            ValueError: Raised when any of the given outputs do not exist in the
                ``Pipeline`` object.


        Returns:
            A new ``Pipeline`` object, containing a subset of the nodes of the
            current one such that only nodes which are directly or transitively
            required to produce the provided outputs are being copied.

        """
        starting = set(outputs)
        result = set()  # type: Set[Node]
        next_nodes = self._get_nodes_with_outputs_transcode_compatible(starting)

        while next_nodes:
            result |= next_nodes
            inputs = set(chain.from_iterable(node.inputs for node in next_nodes))
            starting = inputs

            next_nodes = {
                self._nodes_by_output[_strip_transcoding(output)]
                for output in starting
                if _strip_transcoding(output) in self._nodes_by_output
            }

        return Pipeline(result)

    def from_nodes(self, *node_names: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes which depend
        directly or transitively on the provided nodes.

        Args:
            node_names: A list of node_names which should be used as a
                starting point of the new ``Pipeline``.
        Raises:
            ValueError: Raised when any of the given names do not exist in the
                ``Pipeline`` object.
        Returns:
            A new ``Pipeline`` object, containing a subset of the nodes of
                the current one such that only nodes depending directly or
                transitively on the provided nodes are being copied.

        """

        res = self.only_nodes(*node_names)
        res += self.from_inputs(*map(_strip_transcoding, res.all_outputs()))
        return res

    def to_nodes(self, *node_names: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes required directly
        or transitively by the provided nodes.

        Args:
            node_names: A list of node_names which should be used as an
                end point of the new ``Pipeline``.
        Raises:
            ValueError: Raised when any of the given names do not exist in the
                ``Pipeline`` object.
        Returns:
            A new ``Pipeline`` object, containing a subset of the nodes of the
                current one such that only nodes required directly or
                transitively by the provided nodes are being copied.

        """

        res = self.only_nodes(*node_names)
        res += self.to_outputs(*map(_strip_transcoding, res.all_inputs()))
        return res

    def only_nodes_with_tags(self, *tags: str) -> "Pipeline":
        """Create a new ``Pipeline`` object with the nodes which contain *any*
        of the provided tags. The resulting ``Pipeline`` is empty if no tags
        are provided.

        Args:
            tags: A list of node tags which should be used to lookup
                the nodes of the new ``Pipeline``.
        Returns:
            Pipeline: A new ``Pipeline`` object, containing a subset of the
                nodes of the current one such that only nodes containing *any*
                of the tags provided are being copied.
        """
        tags = set(tags)
        nodes = [node for node in self.nodes if tags & node.tags]
        return Pipeline(nodes)

    def decorate(self, *decorators: Callable) -> "Pipeline":
        """Create a new ``Pipeline`` by applying the provided decorators to
        all the nodes in the pipeline. If no decorators are passed, it will
        return a copy of the current ``Pipeline`` object.

        Args:
            decorators: Decorators to be applied on all node functions in
            the pipeline. Decorators will be applied from right to left.

        Returns:
            A new ``Pipeline`` object with all nodes decorated with the
            provided decorators.

        """
        nodes = [node.decorate(*decorators) for node in self.nodes]
        return Pipeline(nodes)

    def tag(self, tags: Union[str, Iterable[str]]) -> "Pipeline":
        """
        Return a copy of the pipeline, with each node tagged accordingly.
        :param tags: The tags to be added to the nodes.
        :return: New `Pipeline` object.
        """
        nodes = [n.tag(tags) for n in self.nodes]
        return Pipeline(nodes)

    def to_json(self):
        """Return a json representation of the pipeline."""
        transformed = [
            {
                "name": n.name,
                "inputs": list(n.inputs),
                "outputs": list(n.outputs),
                "tags": list(n.tags),
            }
            for n in self.nodes
        ]
        pipeline_versioned = {
            "kedro_version": kedro.__version__,
            "pipeline": transformed,
        }

        return json.dumps(pipeline_versioned)


def _validate_duplicate_nodes(nodes_or_pipes: Iterable[Union[Node, Pipeline]]):
    seen_nodes = set()  # type: Set[str]
    duplicates = defaultdict(set)  # type: Dict[Union[Pipeline, None], Set[str]]

    def _check_node(node_: Node, pipeline_: Pipeline = None):
        name = node_.name
        if name in seen_nodes:
            duplicates[pipeline_].add(name)
        else:
            seen_nodes.add(name)

    for each in nodes_or_pipes:
        if isinstance(each, Node):
            _check_node(each)
        elif isinstance(each, Pipeline):
            for node in each.nodes:
                _check_node(node, pipeline_=each)

    if duplicates:
        duplicates_info = ""

        for pipeline, names in duplicates.items():
            pipe_repr = (
                "Free nodes" if pipeline is None else repr(pipeline).replace("\n", "")
            )
            nodes_repr = "\n".join(f"  - {name}" for name in sorted(names))
            duplicates_info += f"{pipe_repr}:\n{nodes_repr}\n"

        raise ValueError(
            f"Pipeline nodes must have unique names. The following node names "
            f"appear more than once:\n\n{duplicates_info}\nYou can name your "
            f"nodes using the last argument of `node()`."
        )


def _validate_unique_outputs(nodes: List[Node]) -> None:
    outputs = chain.from_iterable(node.outputs for node in nodes)
    outputs = map(_strip_transcoding, outputs)
    duplicates = [key for key, value in Counter(outputs).items() if value > 1]
    if duplicates:
        raise OutputNotUniqueError(
            "Output(s) {} are returned by more than one nodes. Node "
            "outputs must be unique.".format(sorted(duplicates))
        )


def _validate_unique_confirms(nodes: List[Node]) -> None:
    confirms = chain.from_iterable(node.confirms for node in nodes)
    confirms = map(_strip_transcoding, confirms)
    duplicates = [key for key, value in Counter(confirms).items() if value > 1]
    if duplicates:
        raise ConfirmNotUniqueError(
            "{} datasets are confirmed by more than one node. Node "
            "confirms must be unique.".format(sorted(duplicates))
        )


def _validate_transcoded_inputs_outputs(nodes: List[Node]) -> None:
    """Users should not be allowed to refer to a transcoded dataset both
    with and without the separator.
    """
    all_inputs_outputs = set(
        chain(
            chain.from_iterable(node.inputs for node in nodes),
            chain.from_iterable(node.outputs for node in nodes),
        )
    )

    invalid = set()
    for dataset_name in all_inputs_outputs:
        name = _strip_transcoding(dataset_name)
        if name != dataset_name and name in all_inputs_outputs:
            invalid.add(name)

    if invalid:
        raise ValueError(
            "The following datasets are used with transcoding, but "
            "were referenced without the separator: {}.\n"
            "Please specify a transcoding option or "
            "rename the datasets.".format(", ".join(invalid))
        )


def _topologically_sorted(node_dependencies) -> List[Set[Node]]:
    """Topologically group and sort (order) nodes such that no node depends on
    a node that appears in the same or a later group.

    Raises:
        CircularDependencyError: When it is not possible to topologically order
            provided nodes.

    Returns:
        The list of node sets in order of execution. First set is nodes that should
        be executed first (no dependencies), second set are nodes that should be
        executed on the second step, etc.
    """

    def _circle_error_message(error_data: Dict[str, str]) -> str:
        """Error messages provided by the toposort library will
        refer to indices that are used as an intermediate step.
        This method can be used to replace that message with
        one that refers to the nodes' string representations.
        """
        circular = [str(node) for node in error_data.keys()]
        return "Circular dependencies exist among these items: {}".format(circular)

    try:
        return list(toposort(node_dependencies))
    except ToposortCircleError as error:
        message = _circle_error_message(error.data)
        raise CircularDependencyError(message) from error


class CircularDependencyError(Exception):
    """Raised when it is not possible to provide a topological execution
    order for nodes, due to a circular dependency existing in the node
    definition.
    """

    pass
