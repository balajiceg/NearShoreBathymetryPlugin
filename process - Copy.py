from PyQt4.QtCore import *
from PyQt4.QtGui import *
from osgeo import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import numpy as np
import gdal
from osgeo.gdalconst import *
import math
import os
from scipy import ndimage,stats
import matplotlib.pyplot as plt
#########globals
number_band=1
no_data=-999
MNDWI_and_NDVI=1
NDWI=2

np.set_printoptions(threshold=np.inf)

def read_data(filename):
    fileInfo = QFileInfo(filename)
    baseName = fileInfo.baseName()
    layer = QgsRasterLayer(filename, baseName)
    if not layer.isValid():
        print(filename+" layer failed to load!")
    ds = gdal.Open(filename)
    proj = ds.GetProjection()
    geotransform = ds.GetGeoTransform()
    band = ds.GetRasterBand(1)
    no_dat= band.GetNoDataValue()
    array = np.array(band.ReadAsArray())
    XSize,YSize=(band.XSize,band.YSize)
    return array,no_dat,proj,geotransform,XSize,YSize 

def latlngToPix(mx,my,gt):#gt:geotransform param
    col = int((mx - gt[0]) / gt[1])
    row = int((my - gt[3]) / gt[5])
    return (row,col)
    
def get_value(contents,key):
    a=contents.find(key)
    a+=len(key)
    contents=contents[a:]
    contents=contents[:contents.find('\n')]
    contents=contents.replace('=','')
    contents=contents.replace(' ','')
    # print float(contents)
    return float(contents)
    
def convert_toa_cor_reflec(data,meta_file,band_no):
    #OLI band data can also be converted to TOA planetary reflectance 
    #using reflectance rescaling coefficients

    mul_rescale_fac=get_value(meta_file,'REFLECTANCE_MULT_BAND_'+str(band_no))
    add_rescale_fac=get_value(meta_file,'REFLECTANCE_ADD_BAND_'+str(band_no))
    TOA_ref=data*mul_rescale_fac+add_rescale_fac
    
    #TOA reflectance with a correction for the sun angle is then
    sun_elevation=get_value(meta_file,'SUN_ELEVATION')
    # cor_TOA_ref=TOA_ref/math.sin(math.radians(sun_elevation))
    return TOA_ref



blue_file=r"C:\Users\Idiot\Desktop\lansat\subset\blue.tif"
green_file=r"C:\Users\Idiot\Desktop\lansat\subset\green.tif"
red_file=r"C:\Users\Idiot\Desktop\lansat\subset\red.tif"
nir_file=r"C:\Users\Idiot\Desktop\lansat\subset\nir.tif"
swir_file=r"C:\Users\Idiot\Desktop\lansat\subset\swir.tif"

meta_file=r"C:\Users\Idiot\Desktop\lansat\LC08_L1TP_139046_20170115_20170311_01_T1.tar\LC08_L1TP_139046_20170115_20170311_01_T1_MTL.txt"
output_dir=r"C:\Users\Idiot\Desktop\lansat\output"
shape_file=r"C:\Users\Idiot\Desktop\lansat\ground_truth\bathy2.shp"
mask=MNDWI_and_NDVI

#enable gdal Exception printing
gdal.UseExceptions();

#read meata file for conversion of DN to radiance and to reflectence
file = open(meta_file, "r") 
file_contents=file.read() 



    
#progdialog.setValue(5)
#progdialog.setLabelText("reading rasters...")   
#progdialog.setAutoClose(False)
#reading raster
blue = read_data(blue_file)[0]
green = read_data(green_file)[0]

if nir_file is not None:
    nir = read_data(nir_file)[0]
if red_file is not None:
    red=read_data(red_file)[0]
if swir_file is not None:
    swir= read_data(swir_file)[0]

#converting dn to  TOA reflectance
blue=convert_toa_cor_reflec(blue,file_contents,2);
green=convert_toa_cor_reflec(green,file_contents,3);

if red_file is not None:
    red=convert_toa_cor_reflec(red,file_contents,4);
if nir_file is not None:
    nir=convert_toa_cor_reflec(nir,file_contents,5);
if swir_file is not None:
    swir=convert_toa_cor_reflec(swir,file_contents,6);


#progdialog.setValue(10)
#progdialog.setLabelText("Creating Mask...")
#creating mask
if type(mask)==str:
    mask=read_data(mask)
    mask=np.uint8(mask)
else:
    if mask==MNDWI_and_NDVI:
        ndwi=(green-nir)/(green+nir)
        mndwi=(green-swir)/(green+swir)
        ndwi_p_mndwi=(ndwi+mndwi)>0
        ndvi=((nir-red)/(nir+red))>0.1 
        mask=np.logical_and(ndwi_p_mndwi,np.logical_not(ndvi))
        mask=np.uint8(mask)
        del ndwi,mndwi,ndvi,ndwi_p_mndwi
    elif mask==NDWI:
        mask=((green-nir)/(green+nir))>0
        mask=np.uint8(mask)
    #sleving for largest water body
    #grouping [pixels]

    b=np.ones(shape=[3,3],dtype=np.uint8);
    mask, num_features = ndimage.measurements.label(mask,b)
    unique, counts = np.unique(mask, return_counts=True)
    #deleting no data counts
    unique=np.delete(unique,0)
    counts=np.delete(counts,0)
    #find largest group
    pos=np.argmax(counts)
    mask[mask!=unique[pos]] =0
    mask[mask!=0]=1
    mask=np.uint8(mask)

#masking the required bands
blue=mask*blue
green=mask*green


#progdialog.setValue(30)
#progdialog.setLabelText("Computing relative depth...")
#finding relative depth    
n=1000
rel_depth=np.log(n*blue)/np.log(n*green)
#rel_depth_red=np.log(n*green)/np.log(n*red)


#progdialog.setValue(40)
#progdialog.setLabelText("Reading shape file...")
#read shape file and getdata
gt=read_data(green_file)[3]
vlayer = QgsVectorLayer(shape_file, "points", "ogr")
fea=vlayer.getFeatures()
lat=[]
lng=[]
z=[]
rel_z=[]
rel_z_red=[]
for feat in fea:
    attrs = feat.attributes()
    geom = feat.geometry()
    p = geom.asPoint()
    
    x,y=latlngToPix(p[0],p[1],gt)
    if(x>=0 and y>=0 and x<rel_depth.shape[0] and y<rel_depth.shape[1]):
        if(~np.isnan(rel_depth[x,y])):
            lng.append(p[0])
            lat.append(p[1])
            z.append(attrs[0])
            rel_z.append(rel_depth[x,y])
            #rel_z_red.append(rel_depth_red[x,y])

            
#progdialog.setValue(50)
#progdialog.setLabelText("Performing regression...")
#performing regression
reg=stats.linregress(rel_z,z)            
m=reg.slope
c=reg.intercept


#progdialog.setValue(70)
#progdialog.setLabelText("Computing actual depth...")
#actual depth computation
depth=rel_depth*m+c
print np.amin(depth)

#progdialog.setValue(80)
#progdialog.setLabelText("creating regression plot...")
#creating plot
scatter=plt.scatter(rel_z,z)
x=np.linspace(min(rel_z),max(rel_z),10)
plt.plot(x,m*x+c,'r',label='regression line')
plt.legend()
plt.ylabel('Actual depth')
plt.xlabel('Computed relative depth')
plt.figtext(0.75,0.15,"R^2:"+str(round(reg.rvalue**2,4))+"\nStd err:"+str(round(reg.stderr,4)))
#plt.savefig(output_dir+r'\regress_graph.pdf')
#plt.show()

#########################################
#removing layer from canvas
if len(QgsMapLayerRegistry.instance().mapLayers().values())>0:
    for v in QgsMapLayerRegistry.instance().mapLayers().values():
        if (v.id().find('actual')!=-1 or v.id().find('mask')!=-1 or v.id().find('relative')!=-1):
            QgsMapLayerRegistry.instance().removeMapLayer(v.id())
            
            
##getting input raster data to set transformations
_,_,proj,geotransform,XSize,YSize =read_data(green_file)


#progdialog.setValue(90)
#progdialog.setLabelText("Creating output files...")
##creating mask raster
output_file = output_dir+r"\mask.tif"
driver = gdal.GetDriverByName("GTiff")
dst_ds = driver.Create(output_file, 
                       XSize, 
                       YSize, 
                       number_band, 
                       GDT_Byte)
#writting mask raster
dst_ds.GetRasterBand(number_band).WriteArray(mask )
#set no data value
dst_ds.GetRasterBand(number_band).SetNoDataValue(no_data)
#setting extension of mask raster
# top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
dst_ds.SetGeoTransform(geotransform)
# setting spatial reference of mask raster 
srs = osr.SpatialReference(wkt = proj)
dst_ds.SetProjection( srs.ExportToWkt() )




##creating relative depth raster
output_file1 = output_dir+r"\relative_depth.tif"
driver = gdal.GetDriverByName("GTiff")
dst_ds = driver.Create(output_file1, 
                       XSize, 
                       YSize, 
                       number_band, 
                       GDT_Float64)
#writting relative depth raster
dst_ds.GetRasterBand(number_band).WriteArray(rel_depth )
#set no data value
dst_ds.GetRasterBand(number_band).SetNoDataValue(no_data)
#setting extension of relative depth raster
# top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
dst_ds.SetGeoTransform(geotransform)
# setting spatial reference of relative depth raster 
srs = osr.SpatialReference(wkt = proj)
dst_ds.SetProjection( srs.ExportToWkt() )






##creating output raster
output_file2 = output_dir+r"\act_depth.tif"
driver = gdal.GetDriverByName("GTiff")
dst_ds = driver.Create(output_file2, 
                       XSize, 
                       YSize, 
                       number_band, 
                       GDT_Float64)
#writting output raster
dst_ds.GetRasterBand(number_band).WriteArray(depth )
#set no data value
dst_ds.GetRasterBand(number_band).SetNoDataValue(no_data)
#setting extension of output raster
# top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
dst_ds.SetGeoTransform(geotransform)
# setting spatial reference of output raster 
srs = osr.SpatialReference(wkt = proj)
dst_ds.SetProjection( srs.ExportToWkt() )


#Close output raster dataset 
del dst_ds,green,blue,rel_depth,driver

#progdialog.setValue(95)
#progdialog.setLabelText("Adding outputs to canvas...")
#display the output
_=iface.addRasterLayer(output_file, "mask")
_=iface.addRasterLayer(output_file1, "relative depth")
layer=iface.addRasterLayer(output_file2, "actual depth")

fcn = QgsColorRampShader()
fcn.setColorRampType(QgsColorRampShader.INTERPOLATED)
mmax=np.nanmax(depth)
if mmax>20:
    mmax=20.00
lst = [ QgsColorRampShader.ColorRampItem(np.nanmin(depth), QColor(0,255,0)), \
QgsColorRampShader.ColorRampItem(mmax, QColor(255,255,0)) ]
fcn.setColorRampItemList(lst)
shader = QgsRasterShader()
shader.setRasterShaderFunction(fcn)
renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
layer.setRenderer(renderer)


print "completed"
#progdialog.setValue(101)
#progdialog.setLabelText("Completed.")
#progdialog.setCancelButtonText('Ok')
#run_code(blue_file,green_file,meta_file,output_dir,None)

