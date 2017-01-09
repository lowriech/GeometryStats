# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FindSharpAngles
                                 A QGIS plugin
 This plugin creates a shapefile of sharp angles from a given layer
                              -------------------
        begin                : 2016-11-28
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Chris Lowrie
        email                : lowriech@msu.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import numpy as np
from shapely.geometry import LineString, Point
from osgeo import ogr
from PyQt4.QtCore import *
from PyQt4.QtGui import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from find_angles_dialog import FindSharpAnglesDialog
import os.path
from qgis.core import *
import pandas as pd
import math
import tabulate
import matplotlib.pyplot as plt
import matplotlib

class FindSharpAngles:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.layer = ''
        self.fileName = ''
        self.Angles = pd.DataFrame([pd.Series([0,0])], columns = ['Point', 'Angle'])
        self.Edges = pd.DataFrame([pd.Series([0,0])], columns = ['Edge', 'Length'])
        self.fields = QgsFields()
        self.fields.append(QgsField("Angle", QVariant.Double))
        self.sharp_angle_list = []
        self.user_angle = 100.0
        self.count_0 = 0
        self.count_90 = 0
        self.count_180 = 0

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FindSharpAngles_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Find Sharp Angles')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'FindSharpAngles')
        self.toolbar.setObjectName(u'FindSharpAngles')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('FindSharpAngles', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = FindSharpAnglesDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/FindSharpAngles/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Finds sharp angles of a given vector layer'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Find Sharp Angles'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

#######################################################################################################################
#######################################################################################################################

##Supplementary Functions
    def get_path(self):
        fileName = QFileDialog.getSaveFileName()
        self.dlg.path_lbl.setText(fileName)
        self.fileName = fileName
    
    def set_label(self):
        self.dlg.angle_box.setText(str(self.dlg.angle_dial.value()))

    def set_dial(self):
        try:
            self.dlg.angle_dial.setValue(int(self.dlg.angle_box.text()))
        except ValueError:
            pass

    def show_dialog(self, text, severity):
        mw = self.iface.mainWindow()
        QMessageBox.warning(mw, "Sharp Angles", text)

    def calculate_angle(self, p0, p1, p2):
        #Need to manage the unites / projection here
        a = np.array([p0.x, p0.y])
        b = np.array([p1.x, p1.y])
        c = np.array([p2.x, p2.y])
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)
        in_degrees = np.degrees(angle)
        return in_degrees
    
    def calculate_length(self, p0, p1):
        #Need to manage the units / projection here
        return math.sqrt(math.pow(p0.x-p1.x, 2) + math.pow(p0.y-p1.y, 2))

    def load_shape(self, path):
        layer = self.iface.addVectorLayer(path, "Sharp Angles", "ogr")
        self.iface.mapCanvas().refresh()
        return layer

##Primary Functions
    def main(self, user_path, user_angle, layer):
        #Reset the DataFrames
        self.Angles = pd.DataFrame([pd.Series([0,0])], columns = ['Point', 'Angle'])
        self.Edges = pd.DataFrame([], columns = ['Edge', 'Length'])
        
        #Becomes true if the layer is polygonal
        is_polygon = 0
        
        #Work with subselection or entire layer
        selection = layer.selectedFeatures()
        if len(selection)==0:
            selection = layer.getFeatures()
            mw = self.iface.mainWindow()
            self.show_dialog("No features selected, proceeding with entire layer", "Information")
        else:
            self.show_dialog("{} features selected".format(str(len(selection))), "Information")

        #Loop through the selection
        for feature_sub in selection:
            feature = feature_sub.geometry().asPolyline()
            #print(len(feature))
            self.run_component(feature)
        #As of here the Dataframes are both built
        self.angle_stats()
        self.write_pts(user_path)
        #self.edge_stats()

#Generates the DataFrames
    def run_component(self, feature):
        pt_list = []
        #First Create a list of points to iterate
        for i in feature:
            pt_list.append((Point(i)))
        #Next Create a DataFrame of Points and Angles
        if len(pt_list) > 4:
            for i in range(len(pt_list)-2):
                angle = self.calculate_angle(pt_list[i], pt_list[i+1], pt_list[i+2])
                angle = round(angle, 1)
                if angle == 0:
                    self.count_0 += 1
                elif angle < 90.1 and angle > 89.9:
                    self.count_90 += 1
                elif angle >= 179.9:
                    self.count_180 += 1
                entry = pd.Series({'Point':pt_list[i+1], 'Angle':angle})
                self.Angles = self.Angles.append(entry, ignore_index = True)
            angle = self.calculate_angle(pt_list[-2], pt_list[0], pt_list[1])
            angle = round(angle, 1)
            entry = pd.Series({'Point':pt_list[0], 'Angle':angle})
            self.Angles = self.Angles.append(entry, ignore_index = True).dropna()
        
        #Create a DataFrame of Edges and Lengths
        #for i in range(len(pt_list)-2):
        #    length = self.calculate_length(pt_list[i], pt_list[i+1])
        #    entry = pd.Series({"Edge":[pt_list[i],pt_list[i+1]], "Length": length})
        #    self.Edges = self.Edges.append(entry, ignore_index = True)
        #self.Edges = self.Edges.dropna()

#Output the pts to their own shapefile
    def write_pts(self, user_path):
        #Set your own point layer path here
        writer = QgsVectorFileWriter(user_path, "CP1250", self.fields, QGis.WKBPoint, None, "ESRI Shapefile")
        for index, row in self.Angles.iterrows():
            i = row['Point']
            fet = QgsFeature()
            P = QgsPoint(i.x, i.y)
            fet.setGeometry(QgsGeometry.fromPoint(P))
            fet.setAttributes([row['Angle']])
            writer.addFeature(fet)
        del(writer)
        layer = self.load_shape(user_path)
        palyr = QgsPalLayerSettings()
        palyr.readFromLayer(layer)
        palyr.enabled = True
        palyr.fieldName = 'Angle'
        palyr.placement= QgsPalLayerSettings.SymbolAbove
        palyr.setDataDefinedProperty(QgsPalLayerSettings.Size,True,True,'20','')
        palyr.writeToLayer(layer)

    def angle_stats(self):
        mean = np.mean(self.Angles['Angle'])
        std = np.std(self.Angles['Angle'])
        sharpest_10 = np.percentile(self.Angles['Angle'], 10)
        sharpest_25 = np.percentile(self.Angles['Angle'], 25)
        sharpest_50 = np.percentile(self.Angles['Angle'], 50)
        desc_stats = open('/Users/clowrie/Desktop/Descriptive Stats/Descriptive Statistics on {}'.format(self.layer.name()), 'w')
        desc_stats.write('-- Angle Stats --\n')
        desc_stats.write("Average Angle: {}\n10th percentile (Sharpest 10 percent): {}\n25th percentile: {}\nMedian: {}\n\n".format(str(mean),str(sharpest_10),str(sharpest_25),str(sharpest_50)))
        desc_stats.write("Number of 180 degree angles: {}\nNumber of 90 degree angles: {}\nNumber of 0 degree angles: {}".format(self.count_180, self.count_90, self.count_0))
        self.show_dialog("Mean : {}\n10th percentile: {}\n25th percentile: {}\nMedian: {}".format(str(mean),str(sharpest_10),str(sharpest_25),str(sharpest_50)), "X")
        matplotlib.style.use('ggplot')
        plt.figure()
        plt.ylabel('Frequency')
        plt.xlabel('Angle')
        plt.title('Histogram of Angles within {}'.format(self.layer.name()))
        plot_angles = self.Angles['Angle'].plot.hist(bins = 180)
        plt.show()
        #print(self.Angles)
    
    def edge_stats(self):
        mean = np.mean(self.Edges['Length'])
        std = np.std(self.Edges['Length'])
        longest_10 = np.percentile(self.Edges['Length'], 90)
        longest_25 = np.percentile(self.Edges['Length'], 75)
        longest_50 = np.percentile(self.Edges['Length'], 50)

        self.show_dialog("Mean : {}\n90th percentile: {}\n75th percentile: {}\nMedian: {}".format(str(mean),str(longest_10),str(longest_25),str(longest_50)), "X")
        matplotlib.style.use('ggplot')
        plt.figure()
        plt.title('Histogram of Edge Lengths within {}'.format(self.layer.name()))
        plot_angles = self.Edges['Length'].plot.hist(bins = 180)
        plt.show()
        print(self.Edges)
    
    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        layers = self.iface.legendInterface().layers()
        self.dlg.selectLayer.clear()
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.selectLayer.addItems(layer_list)
        
        self.dlg.path_btn.clicked.connect(self.get_path)
        self.dlg.angle_dial.valueChanged.connect(self.set_label)
        self.dlg.angle_box.textEdited.connect(self.set_dial)
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        #user_path = #GET USER PATH FOR OUTPUT PT SHAPEFILE
        #file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        #self.user_angle = #GET USER ANGLE FOR MAXIMUM ANGLE
        # See if OK was pressed
        if result:

            self.user_angle = self.dlg.angle_dial.value()
            self.show_dialog("Outputing points at: {} \n\nPoints less than: {} degrees".format(self.fileName, self.user_angle), "Information")
            selectedLayerIndex = self.dlg.selectLayer.currentIndex()
            self.layer = layers[selectedLayerIndex]
            self.main(self.fileName, self.user_angle, self.layer)
#self.main(user_path, user_angle)

