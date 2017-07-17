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
