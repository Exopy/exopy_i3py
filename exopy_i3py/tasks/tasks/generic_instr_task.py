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
from collections import OrderedDict

from atom.api import (Typed, List, Signal, Str, Callable)

from exopy.tasks.api import InstrumentTask
from exopy.utils.atom_util import (HasPrefsAtom, ordered_dict_to_pref,
                                   ordered_dict_from_pref)


class BaseInstruction(HasPrefsAtom):
    """Base class storing an operation to perform on a driver.

    """
    #: Id of the instruction. Will be used to store the result of the
    #: instruction in the database if meaningful.
    id = Str().tag(pref=True)

    #: Path pointing to the attribute that should be manipulated (get/set/call)
    #: Should start by "driver."
    path = Str().tag(pref=True)

    #: Channel ids that should be inserted in the path to access the proper
    #: attribute.
    ch_ids = Typed(OrderedDict, ()).tag(pref=(ordered_dict_to_pref,
                                              ordered_dict_from_pref))

    def prepare(self):
        """Prepare the instruction for execution.

        Called once in the lifetime, before execute.

        """
        raise NotImplementedError

    def execute(self, task, driver):
        """Execute the instruction on the provided driver.

        """
        raise NotImplementedError

    def get_database_names(self):
        """Get the database names used by the instruction.

        """
        return (self.id,)


class GetInstruction(BaseInstruction):
    """Read the value of an instrument feature and store it in the database.

    """
    def prepare(self):
        """Build the callable accessing driver Feature.

        """
        source = (
            "def _get_(driver, **ch_ids):"
            "    return {path}")
        local = {}
        exec(source.format(', '.join(self.ch_ids), self.path), local)
        self._getter = local['_get_']

    def execute(self, task, driver):
        """Get the value of the Feature and store it in the database.

        """
        ch_ids = {k: task.format_and_eval_string(v)
                  for k, v in self.ch_ids.items()}
        task.write_in_database(self.id, self._getter(driver, **ch_ids))

    # --- Private API ---------------------------------------------------------

    #: Getter function streamlining the process of accessing to the driver
    #: Feature.
    _getter = Callable()


class SetInstruction(BaseInstruction):
    """Set the value of an instrument feature.

    """
    #: Value that should be set when executing the instruction.
    value = Str().tag(pref=True)

    def prepare(self):
        """Build the callable accessing driver Feature.

        """
        source = (
            "def _set_(driver, value, **ch_ids):"
            "    {path} = value")
        local = {}
        exec(source.format(', '.join(self.ch_ids), self.path), local)
        self._setter = local['_set_']

    def execute(self, task, driver):
        """Get the value of the Feature and store it in the database.

        """
        ch_ids = {k: task.format_and_eval_string(v)
                  for k, v in self.ch_ids.items()}
        value = task.format_and_eval_string(self.value)
        task.write_in_database(self.id, self._setter(driver, value, **ch_ids))

    # --- Private API ---------------------------------------------------------

    #: Setter function streamlining the process of accessing to the driver
    #: Feature.
    _setter = Callable()


# XXX add a smooth set instruction


class CallInstruction(BaseInstruction):
    """Call an instrument action and store the result in the database.

    """
    #: List of names to in which to store the return value of the calls.
    #: Their number should match the number of returned values.
    ret_names = List().tag(pref=True)

    #: Arguments to pass to the Action when calling it
    action_kwargs = Typed(OrderedDict, ()).tag(pref=(ordered_dict_to_pref,
                                                     ordered_dict_from_pref))

    def prepare(self):
        """Build the callable accessing driver Feature.

        """
        source = (
            "def _call_(driver, kwargs, **ch_ids):"
            "    return {path}(**kwargs)")
        local = {}
        exec(source.format(', '.join(self.ch_ids), self.path), local)
        self._caller = local['_call_']

    def execute(self, task, driver):
        """Get the value of the Feature and store it in the database.

        """
        ch_ids = {k: task.format_and_eval_string(v)
                  for k, v in self.ch_ids.items()}
        action_kwargs = {k: task.format_and_eval_string(v)
                         for k, v in self.action_kwargs.items()}
        res = self._caller(driver, action_kwargs, **ch_ids)
        if self.ret_names:
            for i, name in enumerate(self.get_names):
                task.write_in_database(name, res[i])
        else:
            task.write_in_database(self.id, res)

    def get_names(self):
        """If return names are provided indicate they are used.

        """
        if self.ret_names:
            return [self.id + '_' + rn for rn in self.ret_names]
        else:
            return (self.id,)

    # --- Private API ---------------------------------------------------------

    #: Caller function streamlining the process of calling a driver Action.
    _setter = Callable()


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
        """Check that all instructions all properly configured.


        """
        pass

    def perform(self):
        """Call all instructions in order.

        """
        for i in self.instructions:
            i.execute(self, self.driver)

    def add_instruction(self, instr):
        """
        """
        pass

    def remove_instruction(self, instr_index):
        """
        """
        pass

    def move_instruction(self, old, new):
        """
        """
        pass
