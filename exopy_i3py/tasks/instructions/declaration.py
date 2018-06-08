# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Exopy-I3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Declarator for instructions.

"""

from atom.api import Unicode, Dict, Property
from enaml.core.api import d_

from exopy.utils.declarator import Declarator, GroupDeclarator, import_and_get
from exopy.utils.traceback import format_exc
from .infos import InstructionInfos


class Instructions(GroupDeclarator):
    """GroupDeclarator for instructions.

    Instructions will be stored according to the group of their parent.

    """
    pass


class Instruction(Declarator):
    """Declarator used to contribute an instruction.

    """
    #: Path to the instruction object. Path should be dot separated and the
    #: class  name preceded by ':'.
    #: ex: exopy_i3py.instructions.bae_instructions:SetInstruction
    #: The path of any parent GroupDeclarator object will be prepended to it.
    #: To update existing InstructionInfos (only instruments and interfaces can
    #: be updated that way), one can specify the name of the top level package
    #: in which the task is defined followed by its name.
    #: ex: exopy_i3py.SetInstruction
    instruction = d_(Unicode())

    #: Path to the view object associated with the instruction.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    #: Metadata associated to the instruction.
    metadata = d_(Dict())

    #: Id of the instruction computed from the top-level package and the name
    id = Property(cached=True)

    def register(self, collector, traceback):
        """Collect instruction and view and add infos to the
        DeclaratorCollector contributions member.

        The group declared by a parent if any is taken into account. All
        Interface children are also registered.

        """
        # Build the task id by assembling the package name and the class name
        instr_id = self.id

        # Determine the path to the task and view.
        path = self.get_path()
        try:
            i_path, instr = (path + '.' + self.instruction
                             if path else self.instruction).split(':')
            v_path, view = (path + '.' + self.view
                            if path else self.view).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            err_id = i_path.split('.', 1)[0] + '.' + instr
            msg = msg % ('view', self.view)

            traceback[err_id] = msg
            return

        # Check that the task does not already exist.
        if instr_id in collector.contributions or instr_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (instr_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(instr, i_path)
            return

        infos = InstructionInfos(metadata=self.metadata)

        # Get the instruction class.
        i_cls = import_and_get(i_path, instr, traceback, instr_id)
        if i_cls is None:
            return

        try:
            infos.cls = i_cls
        except TypeError:
            msg = '{} should a subclass of BaseInstruction.\n{}'
            traceback[instr_id] = msg.format(i_cls, format_exc())
            return

        # Get the instruction view.
        i_view = import_and_get(v_path, view, traceback, instr_id)
        if i_view is None:
            return

        try:
            infos.view = i_view
        except TypeError:
            msg = '{} should a subclass of BaseTaskView.\n{}'
            traceback[instr_id] = msg.format(i_view, format_exc())
            return

        # Add group and add to collector
        infos.metadata['group'] = self.get_group()
        collector.contributions[instr_id] = infos

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            # Remove infos.
            try:
                del collector.contributions[self.id]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = '{} with: instruction: {}, view : {}, metadata: {}'
        return msg.format(type(self).__name__, self.instruction, self.view,
                          self.metadata)

    def _get_id(self):
        """Create the unique identifier of the task using the top level package
        and the class name.

        """
        if ':' in self.instruction:
            path = self.get_path()
            i_path, instr = (path + '.' + self.instruction
                             if path else self.instruction).split(':')

            # Build the instruction id by assembling the package name and the
            # class name
            return i_path.split('.', 1)[0] + '.' + instr

        else:
            return self.instruction
