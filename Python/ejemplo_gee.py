''' Ejercicio 1: Python para el Analisis Espacial

NDVI en una zona de actividad minera (Pastaza)

*********Librerias*********
>> ee --> API para google earth engine (GEE, https://developers.google.com/earth-engine/)
>> pandas --> Libreria para analisis de datos.
>> geopandas --> Extiende las funcionalidades de pandas para el analisis espacial.
>> datetime --> Libreria para crear objetos time.
>> zipfile --> Libreria para manipular archivos zip
>> urllib.request --> Libreria para descargar
>> os --> 
>> matplotlib --> Libreria para realizar graficos
>> numpy --> Linear algebra en python!

#not used:
>> rasterio -->  API bastante intuitiva para la manipulacion de informacion grillada (e.g GeoTIFF).
>> shapely --> Permite manipular geometrias usando en segundo plano GEOS y JTS.
>> fiona -->  estilos estandar para leer y escribir en lugar de clases especificas (e.g OGR).
***************************

'''
import gdal
import pandas as pd
import ee
import geopandas as gpd
import datetime
import os
import zipfile
import urllib.request as request
import matplotlib.pyplot as plt
import numpy as np

ee.Initialize()


output = '/home/aybarpc01/Downloads/lalibertad/'
shapefile = '/home/aybarpc01/Downloads/file_uh/chicama.shp'
figure = '/home/aybarpc01/Downloads/lalibertad/maps/'
os.mkdir(figure)


# 1._Leemos el shapefile con geopandas!!
chicama = gpd.read_file(shapefile)
xmin,ymin,xmax,ymax = chicama.unary_union.bounds # utilizemos un metodo! (recuerda las propiedades de las tuplas!)
gee_bound = '[[%s,%s],[%s,%s],[%s,%s],[%s,%s]]' % (xmin,ymax,xmax,ymax,xmin,ymin,xmax,ymin) 


def downloadNDVI(Iyear,Lyear,gee_bound,output):

    # 2._Seleccionamos landsat puedes cambiar a landsat 8 en https://explorer.earthengine.google.com/
    l5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").filterDate(datetime.datetime(int(Iyear), 1, 1),
                            datetime.datetime(int(Lyear), 12, 31))

    # 3._ De decimal a binarios
    def getQABits(image, start, end, mascara):
        pattern = 0
        for i in range(start,end+1):
            pattern += 2**i
        return image.select([0], [mascara]).bitwiseAnd(pattern).rightShift(start)

    # 4._ Enmascarando nubes y valores dudosos
    def maskQuality(image):
        QA = image.select('pixel_qa')
        sombra = getQABits(QA,3,3,'cloud_shadow')
        nubes = getQABits(QA,5,5,'cloud')
        clean_image = image.updateMask(sombra.eq(0)).updateMask(nubes.eq(0)
        return clean_image
    
    # 5._ Aplicando la misma funcion a todas las imagenes
    ndvi = l5.map(maskQuality).max()
    
    # 6._ Descargando los rasters de ndvi
    path =ndvi.getDownloadUrl({
            'scale': 30,
            'crs': 'EPSG:4326',
            'region': gee_bound})


    ndvi_file = '%s/ndvi.%s.zip' % (output,Iyear)
    request.urlretrieve(path,ndvi_file)
        
    # 7._ Extrayendo y eliminando el zip
    zip_ref = zipfile.ZipFile(ndvi_file, 'r')
    zip_ref.extract(zip_ref.namelist()[1],output)
    dirfull = output + '/' + zip_ref.namelist()[1]
    os.rename(dirfull,output + '/'+ str(Iyear) + '_' + str(Lyear) +'.tif')
    os.remove(ndvi_file)

# 8._ Corriendo nuestra funcion downloadNDVI
for x in range(1984,2012,4):
    downloadNDVI(x,x+4,gee_bound,output)

#9 ._ Creando mapas rapidos!
os.mkdir(figure)
list_files = [output + x for x in os.listdir(output)]
list_files.sort()
list_files.pop()
Range = list(range(1984,2012,4))

#10 ._ Creando mapas simples!
for x in range(0,8):
    grid = Grid.from_raster(list_files[x], data_name='img')
    fig, ax = plt.subplots(figsize=(5,6))
    fig.patch.set_alpha(0)
    plt.imshow(grid.img, extent=grid.extent, cmap='cubehelix', zorder=1)
    plt.colorbar(label='NDVI')
    plt.grid(zorder=0)
    plt.title('NDVI Pastaza '+str(Range[x]))
    plt.xlabel('Longitud')
    plt.ylabel('Latitud')
    figurename = figure+str(Range[x])+'.png'
    plt.savefig(figurename, bbox_inches='tight')

#11 ._ Creando series de tiempo
time  = pd.date_range('1984-01-01', periods=7, freq='4YS')
list_files = [output + x for x in os.listdir(output)]
list_files.sort()
list_files.pop()
mean_values = []
for x in list_files:
    print(x)
    raster = gdal.Open(x)
    raster_np = np.array(raster.GetRasterBand(1).ReadAsArray()).reshape(-1)
    mean_values.append(np.mean(raster_np))

pd_meanNDVI = pd.Series(mean_values,index=time)
pd_meanNDVI.plot()
plt.show()