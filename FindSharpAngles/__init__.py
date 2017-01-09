# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FindSharpAngles
                                 A QGIS plugin
 This plugin creates a shapefile of sharp angles from a given layer
                             -------------------
        begin                : 2016-11-28
        copyright            : (C) 2016 by Chris Lowrie
        email                : lowriech@msu.edu
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
    """Load FindSharpAngles class from file FindSharpAngles.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .find_angles import FindSharpAngles
    return FindSharpAngles(iface)
