# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bathymetry
                                 A QGIS plugin
 Estimate bbathymetry using land sat 8 images
                             -------------------
        begin                : 2017-06-10
        copyright            : (C) 2017 by Balaji
        email                : balaji.9th@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load bathymetry class from file bathymetry.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .bathy import bathymetry
    return bathymetry(iface)
