# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Basic instruction used to define the operations to execute on a driver.

"""
from traceback import format_exc
from collections import OrderedDict

from atom.api import (Typed, List, Dict, Str, Callable, Constant)

from exopy.utils.atom_util import (HasPrefsAtom, ordered_dict_to_pref,
                                   ordered_dict_from_pref)

from ..hinters.base_hinters import (BaseInstructionReturnHinter,
                                    DEP_TYPE as HINTER_DEP_TYPE)

#: Dependency type id
DEP_TYPE = 'exopy_i3py.tasks.instructions'


class BaseInstruction(HasPrefsAtom):
    """Base class storing an operation to perform on a driver.

    """
    #: Identifier for the build dependency collector
    dep_type = Constant(DEP_TYPE).tag(pref=True)

    #: Id of the class, used for persistence.
    instruction_id = Str().tag(pref=True)

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

    #: Hinter responsible for providing a reasonable value for the database
    #: during the checks.
    hinter = Typed(BaseInstructionReturnHinter)

    #: Names under which the instruction ouput should be stored in the database
    database_entries = Dict()

    def check(self, task, driver_cls):
        """Ensure that the path is meaningful and check the hinter.

        Parameters
        ----------
        task : exopy_i3py.tasks.tasks.generic_instr_task.GenericI3pyTask
            Task to which this instruction si attached.

        driver_cls : type
            Driver class with which teh instruction will have to work.

        Returns
        -------
        test : bool
            Whether or not te checks are considered successful

        value_or_errors : dict or str
            Dictionary of values to store in the database if the checks
            succeeded or an error message if something went wrong.

        """
        dr = driver_cls
        valid_path = driver_cls.__name__
        for i, part in enumerate(path.split('.')):
            if i == 0 and part != 'driver':
                return (False,
                        'The path of the instruction should start by "driver"')
            if '[' in part:
                if ']' not in part:
                    return False, 'Malformed channel access: %s' % part
                ch_id = part.split('[')[1].split(']')[0]
                if ch_id not in self.ch_ids:
                    return (False,
                            'Unknown channel id %s, know ids are %s' %
                            (ch_id, self.ch_ids))
                part = part.split('[')[0]

            if not hasattr(dr, part):
                return False, '%s has no attribute %s' % (valid_path, part)

            dr = getattr(dr, part)

        try:
            value = self.hinter.provide_hint(self, driver_cls, task)
        except Exception:
            return (False,
                    'Failed to generate database value hint:\n%s' %
                    format_exc())

        return True, value

    def prepare(self):
        """Prepare the instruction for execution.

        Called once in the lifetime, before execute.

        """
        raise NotImplementedError

    def execute(self, task, driver):
        """Execute the instruction on the provided driver.

        """
        raise NotImplementedError

    def build_from_config(cls, config, dependencies):
        """Build an instruction from a config.

        """
        inst = cls()
        inst.update_members_from_preferences(config)
        hinter_id = config['hinter']['hinter_id']
        hinter_cls = dependencies[HINTER_DEP_TYPE][hinter_id]
        inst.hinter = hinter_cls.build_from_config(config['hinter'],
                                                   dependencies)
        return inst

    # --- Private API ---------------------------------------------------------

    def _default_instruction_id(self):
        """Default value for the instruction_id member.

        """
        pack, _ = self.__module__.split('.', 1)
        return pack + '.' + type(self).__name__


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

    def _default_database_entries(self):
        """Default database names used by the instruction.

        """
        return dict(self.id=1.0)


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
        self._setter(driver, value, **ch_ids)

    # --- Private API ---------------------------------------------------------

    #: Setter function streamlining the process of accessing to the driver
    #: Feature.
    _setter = Callable()


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

    # --- Private API ---------------------------------------------------------

    #: Caller function streamlining the process of calling a driver Action.
    _setter = Callable()

    def _post_setattr_ret_names(self, old, new):
        if new:
            self.database_entries = {self.id + '_' + rn: 1.0 for rn in new}
        else:
            return dict(self.id=1.0)

    def _default_database_entries(self):
        """Default database names used by the instruction.

        """
        return dict(self.id=1.0)
