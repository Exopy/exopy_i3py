# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2018 by ExopyI3py Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Starter for I3py drivers.

"""
from exopy.instruments.api import BaseStarter


class I3pyStarter(BaseStarter):
    """Starter for I3py based drivers.

    """
    def start(self, driver_cls, connection, settings):
        """Pass the connection parameters as keywords and pack settings in

        """
        kwargs, parameters = self.pack_initialize_arguments(connection,
                                                            settings)
        driver = driver_cls(parameters=parameters, **kwargs)
        driver.initialize()
        return driver

    def check_infos(self, driver_cls, connection, settings):
        """Check that we can properly initialize the driver.

        """
        try:
            driver = self.start(driver_cls, connection, settings)
        except Exception:
            return False

        try:
            self.stop(driver)
        except Exception:
            return False

        return True

    def stop(self, driver):
        """Stop the driver by calling finalize.

        """
        driver.finalize()

    def reset(self, driver):
        """Clean the cached value incase th user made a manual modification.

        """
        driver.clear_cache()

    def pack_initialize_arguments(self, connection, settings):
        """Pack the arguments in two dict.

        The first dict is unpacked when calling initialized, the second one is
        passed as 'parameters'

        """
        conn_infos = connection.gather_infos()
        sett_infos = settings.gather_infos()
        sett_infos.pop('id')
        sett_infos.pop('user_id')
        return conn_infos, sett_infos


class I3pyVisaStarter(I3pyStarter):
    """Starter for VISA based drivers.

    """
    def pack_initialize_arguments(self, connection, settings):
        """Pack the arguments in two dict.

        For VISA based instruments, the pyvisa backend needs to be extracted
        from settings and passed outside parameters.

        """
        kwargs, parameters = super().pack_initialize_arguments(connection,
                                                               settings)
        if 'pyvisa_backend' in parameters:
            kwargs['backend'] = parameters.pop('pyvisa_backend')
        return kwargs, parameters


# TODO add a special driver for VISA instrument supporting idn to test
# check_infos
