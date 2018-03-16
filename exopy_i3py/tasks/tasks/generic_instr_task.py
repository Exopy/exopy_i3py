# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task allowing to access any driver Feature/Action of an I3py driver.

"""
from atom.api import List, Signal

from exopy.tasks.api import InstrumentTask
from exopy.utils.container_change import ContainerChange
from exopy.utils.atom_util import update_members_from_preferences

from ..instructions.base_instructions import DEP_TYPE


class GenericI3pyTask(InstrumentTask):
    """Base class for all tasks calling instruments.

    """
    #: List of instruction the task should perform. This list should not be
    #: manipulated by user code.
    instructions = List()

    #: Signal emitted to notify listener that the instructions list has been
    #: modified.
    instruction_changed = Signal()

    def check(self, *args, **kwargs):
        """Check that all instructions are properly configured.


        """
        # XXX need to infer as much as possible from the driver to set
        # reasonable values in the database
        pass

    def perform(self):
        """Call all instructions in order.

        """
        for i in self.instructions:
            i.execute(self, self.driver)

    def add_instruction(self, instruction, index):
        """Add an instruction at the given index.

        Parameters
        ----------
        index : int
            Index at which to insert the new child task.

        instruction : BaseInstruction
            Instruction to insert in the list of instructions.

        """
        self.instructions.insert(index, instruction)

        # In the absence of a root task do nothing else than inserting the
        # child.
        if self.has_root:

            # Register the new entries in the database
            db_entries = self.database_entries.copy()
            db_entries.update(instruction.database_entries)
            self.database_entries = db_entries
            instruction.observe('database_entries',
                                self._react_to_instr_database_entries_change)

            # Register anew preferences to keep the right ordering for the
            # instructions
            self.register_preferences()

            change = ContainerChange(obj=self, name='instructions',
                                     added=[(index, instruction)])
            self.instruction_changed(change)

    def remove_instruction(self, index):
        """Remove an instruction from the instructions list.

        Parameters
        ----------
        index : int
            Index at which the instruction to remove is located.

        """
        instruction = self.instructions.pop(index)

        # Cleanup database
        db_entries = self.database_entries.copy()
        for k in db_entries:
            if k in instruction.database_entries:
                del db_entries[k]
        self.database_entries = db_entries
        instruction.unobserve('database_entries',
                              self._react_to_instr_database_entries_change)

        # Update preferences
        self.register_preferences()

        change = ContainerChange(obj=self, name='instructions',
                                 removed=[(index, instruction)])
        self.instruction_changed(change)

    def move_instruction(self, old, new):
        """Move an instruction.

        Parameters
        ----------
        old : int
            Index at which the instruction to move is currently located.

        new : BaseTask
            Index at which to insert the instruction.

        """
        instruction = self.instructions.pop(old)
        self.instructions.insert(new, instruction)

        # In the absence of a root task do nothing else than moving the
        # child.
        if self.has_root:
            # Register anew preferences to keep the right ordering for the
            # children
            self.register_preferences()

            change = ContainerChange(obj=self, name='instructions',
                                     moved=[(old, new, instruction)])
            self.instruction_changed(change)

    def register_preferences(self):
        """Create the task entries in the preferences object.

        """
        super(GenericI3pyTask, self).register_preferences()

        # Register the instructions
        for i, instr in enumerate(self.instructions):
            child_id = 'instruction_{}'.format(i)
            self.preferences[child_id] = instr.preferences_from_members()

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding..

        """
        task = cls()
        update_members_from_preferences(task, config)

        # Collect and build the instructions
        i = 0
        pref = 'instruction_{}'
        instructions = []
        while True:
            instr_name = pref.format(i)
            if instr_name not in config:
                break
            instr_config = config[instr_name]
            instr_class_name = instr_config.pop('instruction_id')
            instr_cls = dependencies[DEP_TYPE][instr_class_name]
            instr = instr_cls.build_from_config(instr_config,
                                                dependencies)
            instructions.append(instr)
            i += 1

        task.instructions = instructions

        return task

    def traverse(self, depth=-1):
        """Yield a task and all of its components.

        The base implementation simply yields the task itself.

        Parameters
        ----------
        depth : int
            How deep should we explore the tree of tasks. When this number
            reaches zero deeper children should not be explored but simply
            yielded.

        """
        yield self
        for instr in self.instructions:
            yield instr

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _react_to_instr_database_entries_change(self, change):
        """Update the database entries whenever an instruction modify its used
        names.

        """
        db_entries = self.database_entries.copy()
        if 'old_value' in change:
            for k in db_entries:
                if k in change['object'].database_entries:
                    del db_entries[k]
        db_entries.update(change['value'])
        self.database_entries = db_entries
