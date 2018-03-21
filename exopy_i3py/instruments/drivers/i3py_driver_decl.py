# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by ExopyI3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Custom declaration for I3py driver.

"""
from exopy.instruments.api import Driver


class DummyCollector:
    """Dummy collector used to avoid setting the driver infos early.

    """
    __slots__ = ('contributions')


INTERFACE_MAP = {'ASRL': 'VisaRS232', 'GPIB': 'VisaGPIB',
                 'TCPIP': 'VisaTCPIP', 'USB': 'VisaUSB'}


class I3pyVisaDriver(Driver):
    """Custom declarator pulling the connection infos from the driver class.

    """

    def register(self, collector, traceback):
        """Use the driver class variables to fill in the connections.

        """
        dummy = DummyCollector()
        dummy.contributions = collector.contributions.copy()
        super().register(dummy, traceback)

        if self.is_registered:
            infos = dummy.contributions[self.id]
            interfaces = infos.cls.INTERFACES
            conns = self.connections.copy()
            for interface_type, details in interfaces.items():
                if (interface_type in INTERFACE_MAP and
                        interface_type not in conns):
                    conns[INTERFACE_MAP[interface_type]] = details

            self.connections = conns
            infos.connections = conns

            collector.contributions[self.id] = infos
