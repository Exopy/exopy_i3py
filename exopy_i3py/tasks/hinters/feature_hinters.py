# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Exopy-I3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Hinters for the standard features of I3py.

Those should do their job in most cases (at least as long as the driver does
not do some crazy modification to the return value)

"""
from .base_hinters import BaseInstructionReturnHinter


# TODO implement
class FeatureHinter():
    """Base Feature hinter guessing what it can from the creation kwargs.

    """
    pass


class EnumeratedFeatureHinter():
    """Provide hints for Feature with a discrete set of allowed values.

    """
    pass


class LimitsValidatedHinter():
    """Provide hints for Feature limit handling.

    Note that if the limit is dynamic in nature, we may not be able to give a
    reasonable value.

    """
    pass


class WithUnitHinter():
    """Hinter handling float with units.

    """
    pass


class RegisterHinter():
    """Hinter specialized in handling Register features.

    """
    pass


# TODO this one is more work bacause it has a nested hinter.
# TODO requires also a more complex selection logic
class AliasHinter():
    """Hinter specialized in handling Alias features.

    """
    pass
