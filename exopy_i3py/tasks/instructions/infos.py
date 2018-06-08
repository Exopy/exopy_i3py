# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by ExopyI3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Object used to store instructions.

"""
from atom.api import Atom, Subclass, Dict
import enaml

from .base_instructions import BaseInstruction

with enaml.imports():
    from .views.base_instruction_views import BaseInstructionView


class InstructionInfos(Atom):
    """Base infos for tasks and interfaces.

    """
    #: Class representing this task.
    cls = Subclass(BaseInstruction)

    #: Widget associated with this task.
    view = Subclass(BaseInstructionView)

    #: Metadata associated with this task such as group, looping capabilities,
    #: etc
    metadata = Dict()
