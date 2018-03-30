# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by Exopy-I3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Hinters for the standard actions of I3py.

Those should do their job well if the action are annotated with easy to
understand types. The main issue will probably be with structured array as
output.

"""
from .base_hinters import BaseInstructionReturnHinter

# XXX implement
class ActionSignatureHinter(BaseInstructionReturnHinter):
    """Hinter relying on the Action signature nd modifiers to make a guess.

    """
    pass


class RegisterActionHinter(BaseInstructionReturnHinter):
    """Hinter specialized for RegisterAction.

    """
    pass
