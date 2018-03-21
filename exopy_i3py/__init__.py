# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018-2018 by ExopyI3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Package allowing a seemless integration of I3py in Exopy.

"""
import enaml


def list_manifests():
    """List all the manifest contributed by the package.

    """
    with enaml.imports():
        from .instruments.manifest import I3pyInstrManifest
        from .tasks.manifest import I3pyTaskManifest

    return [I3pyInstrManifest, I3pyTaskManifest]
