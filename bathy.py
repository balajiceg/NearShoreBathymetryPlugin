# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bathymetry
                                 A QGIS plugin
 Estimate bbathymetry using land sat 8 images
                              -------------------
        begin                : 2017-06-10
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Balaji
        email                : balaji.9th@gmail.com
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import resources
from bathy_dialog import bathymetryDialog
import os.path
from osgeo import *
from process import *

import numpy as np
import gdal
from osgeo.gdalconst import *
import math
from scipy import ndimage,stats
import matplotlib.pyplot as plt

class bathymetry:
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



        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'bathymetry_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Bathymetry using landsat 8')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'bathymetry')
        self.toolbar.setObjectName(u'bathymetry')

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
        return QCoreApplication.translate('bathymetry', message)


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
        self.dlg = bathymetryDialog()

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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/bathymetry/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Bathymetry landsat'),
            callback=self.run,
            parent=self.iface.mainWindow())
		
	QObject.connect(self.dlg.blue_btn,SIGNAL("clicked()"),self.Browseinputfileblue)
        QObject.connect(self.dlg.green_btn,SIGNAL("clicked()"),self.Browseinputfilegreen)
        QObject.connect(self.dlg.meta_data_btn,SIGNAL("clicked()"),self.Browseinputmetafile)
        QObject.connect(self.dlg.output_dir_btn,SIGNAL("clicked()"),self.Browseoutputfile)
	QObject.connect(self.dlg.ok,SIGNAL("clicked()"),self.go)
        QObject.connect(self.dlg.cancel,SIGNAL("clicked()"),self.close)
        QObject.connect(self.dlg.shape_file_btn,SIGNAL("clicked()"),self.Browseshapefile)
        QObject.connect(self.dlg.nir_btn,SIGNAL("clicked()"),self.Browseinputfilenir)
        QObject.connect(self.dlg.swir_btn,SIGNAL("clicked()"),self.Browseinputfileswir)
        QObject.connect(self.dlg.red_btn,SIGNAL("clicked()"),self.Browseinputfilered)
        QObject.connect(self.dlg.mask_btn,SIGNAL("clicked()"),self.Browseinputfilemask)
        

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Bathymetry using landsat 8'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def close(self):
        self.dlg.done(0) 

    def Browseinputfileblue(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.TIFF *.TIF *.tif *.tiff")
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.blue.setText(filenames[0])      
            self.blue_file=filenames[0]
    
    def Browseinputfilegreen(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.TIFF *.TIF *.tif *.tiff")
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.green.setText(filenames[0])
            self.green_file=filenames[0]
    
    def Browseinputfilenir(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.TIFF *.TIF *.tif *.tiff")
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.nir.setText(filenames[0])
            self.nir_file=filenames[0]
    
    
    def Browseinputfileswir(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.TIFF *.TIF *.tif *.tiff")
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.swir.setText(filenames[0])
            self.swir_file=filenames[0]
    
    def Browseinputfilered(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.TIFF *.TIF *.tif *.tiff")
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.red.setText(filenames[0])
            self.red_file=filenames[0]
            
    def Browseinputfilemask(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.TIFF *.TIF *.tif *.tiff")
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.mask.setText(filenames[0])
            self.mask_file=filenames[0]
    
    
    
    
    
    def Browseinputmetafile(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.txt *.TXT")
        
        fd.setFilters(ext_names)
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.meta_data.setText(filenames[0])
            self.meta_file=filenames[0]
    
    
    
       
    def Browseoutputfile(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.Directory)
        
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.output_dir.setText(filenames[0])  
            self.output_dir=filenames[0]
    
    def Browseshapefile(self):
        fd=QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        ext_names=list()
        ext_names.append("*.shp *.SHP")
        filenames = list()		
        if fd.exec_():
            filenames = fd.selectedFiles()
            self.dlg.shape_file.setText(filenames[0])  
            self.shape_file=filenames[0]
            
    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.label.setStyleSheet("background: white")
        self.dlg.label.setWordWrap(True);
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
            
    def read_all(self):
        self.output_dir=self.dlg.output_dir.text()
        self.blue_file=self.dlg.blue.text()
        self.green_file=self.dlg.green.text()
        self.red_file=self.dlg.red.text()
        self.nir_file=self.dlg.nir.text()
        self.swir_file=self.dlg.swir.text()
        self.mask_file=self.dlg.mask.text()
        self.meta_file=self.dlg.meta_data.text()
        self.shape_file=self.dlg.shape_file.text()
            
    def go(self):
        progdialog = QProgressDialog("Processing...","Cancel", 0, 101,self.dlg)
        progdialog.setWindowTitle("Processing")
        
        progdialog.setValue(0)
        progdialog.setLabelText("calling algorithm")
        
        self.read_all()
        
        if self.dlg.landsat8.isChecked():
            satellite=8
        else:
            satellite=7
        
        blue_bn=self.dlg.blue_bn.value()
        green_bn=self.dlg.green_bn.value()
        red_bn=self.dlg.red_bn.value()
        nir_bn=self.dlg.nir_bn.value()
        swir_bn=self.dlg.swir_bn.value()

        toa_conv_needed=self.dlg.toa.isChecked()
        sieve_largest_polygon=self.dlg.sieve.isChecked()


        progdialog.setWindowModality(Qt.WindowModal)
        progdialog.show()

        if self.dlg.ndwi.isChecked():
            mask=NDWI
            run_code(self.blue_file,self.green_file,None,self.nir_file,None,self.meta_file,self.output_dir,self.shape_file,mask,progdialog,satellite,blue_bn,green_bn,red_bn,nir_bn,swir_bn,toa_conv_needed,sieve_largest_polygon)
        elif self.dlg.mndwi.isChecked():
            mask=MNDWI_and_NDVI
            run_code(self.blue_file,self.green_file,self.red_file,self.nir_file,self.swir_file,self.meta_file,self.output_dir,self.shape_file,mask,progdialog,satellite,blue_bn,green_bn,red_bn,nir_bn,swir_bn,toa_conv_needed,sieve_largest_polygon)
        else:
            mask=self.mask_file
            run_code(self.blue_file,self.green_file,None,None,None,self.meta_file,self.output_dir,self.shape_file,mask,progdialog,satellite,blue_bn,green_bn,red_bn,nir_bn,swir_bn,toa_conv_needed,sieve_largest_polygon)
    
   
        
     