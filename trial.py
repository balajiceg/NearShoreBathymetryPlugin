from PyQt4.QtCore import *
from osgeo import *
import numpy as np
import gdal
from osgeo.gdalconst import *
import math
import os
from scipy import ndimage

np.set_printoptions(threshold=np.inf)

def classify(data,sel_val):
    classified=np.zeros(data.shape,np.uint16)
    class_i=0
    for i in range(1,data.shape[0]-1):
        print i
        for j in range(1,data.shape[1]-1):
            if (classified[i,j]==0) :
                if data[i,j]==sel_val:
                    val=data[i,j]
                    class_i+=1
                    stack=[]
                    stack.append([i,j])
                    classified[i,j]=class_i
                    while(len(stack)>0):
                        [l,m]=stack.pop()
                        if(l>0 and l<data.shape[0]-1 and m>0 and m<data.shape[1]-1):
                            if(data[l-1,m-1]==val and classified[l-1,m-1]==0):
                                stack.append([l-1,m-1])
                                classified[l-1,m-1]=class_i
                            if(data[l-1,m]==val and classified[l-1,m]==0):
                                stack.append([l-1,m])
                                classified[l-1,m]=class_i
                            if(data[l-1,m+1]==val and classified[l-1,m+1]==0):
                                stack.append([l-1,m+1])
                                classified[l-1,m+1]=class_i
                            if(data[l,m-1]==val and classified[l,m-1]==0):
                                stack.append([l,m-1])
                                classified[l,m-1]=class_i
                            if(data[l,m+1]==val and classified[l,m+1]==0):
                                stack.append([l,m+1])
                                classified[l,m+1]=class_i
                            if(data[l+1,m+1]==val and classified[l+1,m+1]==0):
                                stack.append([l+1,m+1])
                                classified[l+1,m+1]=class_i
                            if(data[l+1,m]==val and classified[l+1,m]==0):
                                stack.append([l+1,m])
                                classified[l+1,m]=class_i
                            if(data[l+1,m-1]==val and classified[l+1,m-1]==0):
                                stack.append([l+1,m-1])
                                classified[l+1,m-1]=class_i
    return classified



def latlonToPix(mx,my,gt):#gt:geotransform param
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
    print float(contents)
    return float(contents)
    
def convert_toa_cor_reflec(data,meta_file,band_no):
    #OLI band data can also be converted to TOA planetary reflectance 
    #using reflectance rescaling coefficients

    mul_rescale_fac=get_value(meta_file,'REFLECTANCE_MULT_BAND_'+str(band_no))
    add_rescale_fac=get_value(meta_file,'REFLECTANCE_ADD_BAND_'+str(band_no))
    TOA_ref=data*mul_rescale_fac+add_rescale_fac
    
    #TOA reflectance with a correction for the sun angle is then
    sun_elevation=get_value(meta_file,'SUN_ELEVATION')
    cor_TOA_ref=TOA_ref/math.sin(math.radians(sun_elevation))
    return cor_TOA_ref



blue_file=r"C:\Users\Idiot\Desktop\lansat\subset\mndwi_p_ndwi.tif"
green_file=r"C:\Users\Idiot\Desktop\lansat\subset\green.tif"
meta_file=r"C:\Users\Idiot\Desktop\lansat\LC08_L1TP_139046_20170115_20170311_01_T1.tar\LC08_L1TP_139046_20170115_20170311_01_T1_MTL.txt"
output_dir=r"C:\Users\Idiot\Desktop\lansat\output"
shape_file=r"C:\Users\Idiot\Desktop\lansat\ground_truth\bathy.shp"

#def run_code(blue_file,green_file,meta_file,output_dir,shp_file,progdialog):
gdal.UseExceptions();

#reading raster
fileInfo = QFileInfo(blue_file)
baseName = fileInfo.baseName()
blue = QgsRasterLayer(blue_file, baseName)
if not blue.isValid():
  print "blue layer failed to load!"

fileInfo = QFileInfo(green_file)
baseName = fileInfo.baseName()
green = QgsRasterLayer(green_file, baseName)
if not green.isValid():
  print "green failed to load!"


ds = gdal.Open(green_file)
ds1 = gdal.Open(blue_file,GA_ReadOnly)

    
#Get projection
prj = ds.GetProjection()
#setting band
number_band = 1
#Get raster metadata
geotransform = ds.GetGeoTransform()


green = ds.GetRasterBand(number_band)
blue = ds1.GetRasterBand(number_band)
no_data= green.GetNoDataValue()

green_np = np.array(green.ReadAsArray())
blue_np = np.array(blue.ReadAsArray())
data=blue_np
b=np.ones(shape=[3,3],dtype=np.uint8);
l, num_features = ndimage.measurements.label(data,b)
unique, counts = np.unique(l, return_counts=True)
unique=np.delete(unique,0)
counts=np.delete(counts,0)
pos=np.argmax(counts)
l[l!=unique[pos]] =0
l[l!=0]=1 
 
#out=classify(data,1)
out=l



#########################################
#removing layer from canvas
if len(QgsMapLayerRegistry.instance().mapLayers().values())>0:
    id=QgsMapLayerRegistry.instance().mapLayers().values()[0].id()
    if id.find('result')==0:
        QgsMapLayerRegistry.instance().removeMapLayer(id)
##creating output raster
output_file = output_dir+r"\output12.tif"
driver = gdal.GetDriverByName("GTiff")
dst_ds = driver.Create(output_file, 
                       green.XSize, 
                       green.YSize, 
                       number_band, 
                       GDT_Int16  )


#writting output raster
dst_ds.GetRasterBand(number_band).WriteArray(out )
#set no data value
dst_ds.GetRasterBand(number_band).SetNoDataValue(-1)
#setting extension of output raster
# top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
dst_ds.SetGeoTransform(geotransform)
# setting spatial reference of output raster 
srs = osr.SpatialReference(wkt = prj)
dst_ds.SetProjection( srs.ExportToWkt() )

#Close output raster dataset 
del dst_ds,green_np,blue_np,out
#display the output
iface.addRasterLayer(output_file, "result")
print "complete"
#run_code(blue_file,green_file,meta_file,output_dir,None)

