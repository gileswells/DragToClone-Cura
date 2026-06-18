# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import copy
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from UM.Application import Application
from UM.Extension import Extension
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.Operation import Operation
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection

# Supported tools
_CLONE_ON_DRAG_TOOLS = {"TranslateTool", "RotateTool"}


class _AddClonesOperation(Operation):
    """Leaves a clone at the original location when a user holds down
    Alt/Option when starting a move/rotate operation.

    This operation merges with whatever operation the active tool just pushed
    for the drag (e.g. a TranslateOperation or RotateOperation), combining "add
    the clone" and "move/rotate the original" into a single undo step. This
    pattern mirrors how cura.Operations.PlatformPhysicsOperation works, which
    merges its post-drop adjustment into the preceding drag operation in the
    same way.
    """

    def __init__(self, nodes_and_parents: List[Tuple[SceneNode, SceneNode]], mergeable: bool) -> None:
        super().__init__()
        self._nodes_and_parents = nodes_and_parents
        if mergeable:
            self._always_merge = True

    def undo(self) -> None:
        for node, _parent in self._nodes_and_parents:
            node.setParent(None)

    def redo(self) -> None:
        for node, parent in self._nodes_and_parents:
            node.setParent(parent)

    def mergeWith(self, other: Operation) -> Optional[GroupedOperation]:
        if not getattr(self, "_always_merge", False):
            return None

        group = GroupedOperation()
        group.addOperation(other)
        group.addOperation(self)
        return group


class DragToClone(Extension):
    def __init__(self) -> None:
        super().__init__()

        controller = Application.getInstance().getController()
        controller.toolOperationStarted.connect(self._onToolOperationStarted)
        controller.toolOperationStopped.connect(self._onToolOperationStopped)

        self._operation_stack = Application.getInstance().getOperationStack()
        self._operation_stack.changed.connect(self._onOperationStackChanged)

        # Clones prepared for the drag currently in progress, if any. They are
        # parented into the scene immediately (so they're visible during the
        # drag), but only registered on the undo stack once the drag finishes.
        self._pending_clones: Optional[List[Tuple[SceneNode, SceneNode]]] = None
        # Whether the operation stack changed since the drag started, i.e.
        # whether the active tool actually pushed a move/rotate operation.
        self._stack_changed_during_drag = False

    def _onOperationStackChanged(self) -> None:
        if self._pending_clones is not None:
            self._stack_changed_during_drag = True

    def _onToolOperationStarted(self, tool) -> None:
        if tool.getPluginId() not in _CLONE_ON_DRAG_TOOLS:
            return

        if not QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier:
            return

        if not Selection.hasSelection():
            return

        top_level_nodes: List[SceneNode] = []
        for node in Selection.getAllSelectedObjects():
            current_node = node
            while current_node.getParent() and current_node.getParent().callDecoration("isGroup"):
                current_node = current_node.getParent()

            if current_node not in top_level_nodes:
                top_level_nodes.append(current_node)

        pending_clones: List[Tuple[SceneNode, SceneNode]] = []
        for node in top_level_nodes:
            new_node = copy.deepcopy(node)

            build_plate_number = node.callDecoration("getBuildPlateNumber")
            new_node.callDecoration("setBuildPlateNumber", build_plate_number)
            for child in new_node.getChildren():
                child.callDecoration("setBuildPlateNumber", build_plate_number)

            # Parent it immediately so the clone is visible for the whole drag.
            # Registering it on the undo stack is deferred until the drag
            # completes, see _onToolOperationStopped().
            parent = node.getParent()
            new_node.setParent(parent)
            pending_clones.append((new_node, parent))

        self._pending_clones = pending_clones
        self._stack_changed_during_drag = False

    def _onToolOperationStopped(self, tool) -> None:
        if self._pending_clones is None:
            return

        # If the tool pushed a move/rotate operation for this drag, merge our
        # "add the clone" operation into it so a single undo reverts both the
        # clone and the drag. Otherwise (e.g. the user clicked without
        # dragging), just register the clone on its own.
        operation = _AddClonesOperation(self._pending_clones, mergeable = self._stack_changed_during_drag)
        operation.push()

        self._pending_clones = None
        self._stack_changed_during_drag = False
