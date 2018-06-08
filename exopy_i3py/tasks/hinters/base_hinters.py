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
from inspect import cleandoc

from atom.api import Str, List, Value, Dict, Property
from enaml.core.api import d_

from exopy.utils.declarator import Declarator, GroupDeclarator, import_and_get
from exopy.utils.traceback import format_exc

from atom.api import Constant

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


# XXX write logic here: copy from tasks
class InstructionReturnHint(Declarator):
    """Declaration for a hinter specifying its location and associated view.

    """


class Tasks(GroupDeclarator):
    """GroupDeclarator for tasks.

    Tasks will be stored according to the group of their parent.

    """
    pass


class Task(Declarator):
    """Declarator used to contribute a task.

    """
    #: Path to the task object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: ex: exopy.tasks.tasks.logic.loop_task:LoopTask
    #: The path of any parent GroupDeclarator object will be prepended to it.
    #: To update existing TaskInfos (only instruments and interfaces can be
    #: updated that way), one can specify the name of the top level package
    #: in which the task is defined followed by its name.
    #: ex: exopy.LoopTask
    task = d_(Str())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Str())

    #: Metadata associated to the task. ex : loopable = True
    metadata = d_(Dict())

    #: List of supported driver ids.
    instruments = d_(List())

    #: Runtime dependencies analyser ids corresponding to the runtime
    #: dependencies of the task (there is no need to list the instruments
    #: related dependencies as those are handled in a different fashion).
    dependencies = d_(List())

    #: Id of the task computed from the top-level package and the task name
    id = Property(cached=True)

    def register(self, collector, traceback):
        """Collect task and view and add infos to the DeclaratorCollector
        contributions member.

        The group declared by a parent if any is taken into account. All
        Interface children are also registered.

        """
        # Build the task id by assembling the package name and the class name
        task_id = self.id

        # If the task only specifies a name update the matching infos.
        if ':' not in self.task:
            if self.task not in collector.contributions:
                collector._delayed.append(self)
                return

            infos = collector.contributions[task_id]
            infos.instruments.update(self.instruments)
            infos.dependencies.update(self.dependencies)
            infos.metadata.update(self.metadata)

            check = check_children(self)
            if check:
                traceback[task_id] = check
                return

            for i in self.children:
                i.register(collector, traceback)
            self.is_registered = True
            return

        # Determine the path to the task and view.
        path = self.get_path()
        try:
            t_path, task = (path + '.' + self.task
                            if path else self.task).split(':')
            v_path, view = (path + '.' + self.view
                            if path else self.view).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            err_id = t_path.split('.', 1)[0] + '.' + task
            msg = msg % ('view', self.view)

            traceback[err_id] = msg
            return

        # Check that the task does not already exist.
        if task_id in collector.contributions or task_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (task_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(task, t_path)
            return

        infos = TaskInfos(metadata=self.metadata,
                          dependencies=self.dependencies,
                          instruments=self.instruments)

        # Get the task class.
        t_cls = import_and_get(t_path, task, traceback, task_id)
        if t_cls is None:
            return

        try:
            infos.cls = t_cls
        except TypeError:
            msg = '{} should a subclass of BaseTask.\n{}'
            traceback[task_id] = msg.format(t_cls, format_exc())
            return

        # Get the task view.
        t_view = import_and_get(v_path, view, traceback, task_id)
        if t_view is None:
            return

        try:
            infos.view = t_view
        except TypeError:
            msg = '{} should a subclass of BaseTaskView.\n{}'
            traceback[task_id] = msg.format(t_view, format_exc())
            return

        # Check children type.
        check = check_children(self)
        if check:
            traceback[task_id] = check
            return

        # Add group and add to collector
        infos.metadata['group'] = self.get_group()
        collector.contributions[task_id] = infos

        # Register children.
        for i in self.children:
            i.register(collector, traceback)

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            # Unregister children.
            for i in self.children:
                i.unregister(collector)

            # If we were just extending the task, clean instruments.
            if ':' not in self.task:
                if self.task in collector.contributions:
                    infos = collector.contributions[self.task]
                    infos.instruments -= set(self.instruments)
                    infos.dependencies -= set(self.dependencies)

                return

            # Remove infos.
            try:
                # Unparent remaining interfaces
                infos = collector.contributions[self.id]
                for i in infos.interfaces.values():
                    i.parent = None

                del collector.contributions[self.id]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       task: {}, view : {}, metadata: {} and instruments {}
                       declaring :
                       {}''')
        return msg.format(type(self).__name__, self.task, self.view,
                          self.metadata, self.instruments,
                          '\n'.join(' - {}'.format(c) for c in self.children))

    def _get_id(self):
        """Create the unique identifier of the task using the top level package
        and the class name.

        """
        if ':' in self.task:
            path = self.get_path()
            t_path, task = (path + '.' + self.task
                            if path else self.task).split(':')

            # Build the task id by assembling the package name and the class
            # name
            return t_path.split('.', 1)[0] + '.' + task

        else:
            return self.task
