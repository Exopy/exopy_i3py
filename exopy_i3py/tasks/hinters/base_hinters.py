# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Exopy-I3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Basic hinter trying to provide a meaningful return value for an instruction.

"""
from atom.api import Value, Str, Constant

from exopy.utils.declarator import Declarator
from exopy.utils.atom_util import HasPrefsAtom


#: Dependency type id
DEP_TYPE = 'exopy_i3py.tasks.hinters'


class BaseInstructionReturnHinter(HasPrefsAtom):
    """Base hinter unable to guess anything useful.

    """
    #: Identifier for the build dependency collector
    dep_type = Constant(DEP_TYPE).tag(pref=True)

    #: Id of the class, used for persistence.
    hinter_id = Str().tag(pref=True)

    #: Value provided by the user as a formula to be evaluated by a task.
    user_value = Str().tag(pref=True)

    #: Value guessed from the information extracted from the driver.
    guessed_value = Value()

    @classmethod
    def rate_hint_pertinence(cls, instruction, driver):
        """Determine if this particular hinter class is well suited for the
        instruction.

        The rating should be an integer, the higher the better.

        """
        return 0

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Build the hinter from config.

        """
        hinter = cls()
        hinter.update_members_from_preferences(config)
        return hinter

    def guess_value(self, instruction, driver):
        """Guess a reasonable hint value based on the driver introspection.

        """
        pass

    def provide_hint(self, instruction, driver_cls, task):
        """By default simply provide the user value of the guessed one.

        This method assumes the instruction writes a single value in the
        database.

        Parameters
        ----------
        instruction:
            Instruction to which this hinter is attached.

        driver_cls:
            Class of the driver the instruction will have to operate with.

        task:
            Task to which teh parent instruction belong.

        Returns
        -------
        database_values: dict
            Dictionary of the hints matching the database values of the
            instruction.

        """
        if self.user_value:
            val = task.format_and_eval_string(self.user_value)
        else:
            val = self.guessed_value
        return {instruction.database_entries.keys()[0]: val}

    # --- Private API ---------------------------------------------------------

    def _default_hinter_id(self):
        """Default value for the hinter_id member.

        """
        pack, _ = self.__module__.split('.', 1)
        return pack + '.' + type(self).__name__


# XXX write logic here
class InstructionReturnHint(Declarator):
    """Declaration for a hinter specifying its location and associated view.

    """
    pass
