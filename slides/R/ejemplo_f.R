rm(list = ls())
library(gstat)
library(automap)
library(raster)
library(sf)
library(dplyr)

load('/home/aybarpc01/Downloads/shp/PISCOp_raingauge_database.Rdata.crdownload')
# Creando serie de timepo
sq_date <- seq(as.Date('1981-01-01'),as.Date('2018-08-01'),by = 'month')
# Observacione mensuales
datos_obs <- PISCOp_raingauge_database$unstable$plausible
# Datos espaciales de PISCO
data_sp <- PISCOp_raingauge_database$spatial
# convertimos de SP a SF
data_sf <- st_as_sf(data_sp)
# Creamo un campo ID
data_sf <- data_sf %>% mutate(id=1:496)
# Cargamos los ShapeFile
UH_ANA <- read_sf("/home/aybarpc01/Downloads/shp/UH.shp")
# Seleecionamos la cuenca ALTO APURIMAC
Apurimac <- UH_ANA %>% 
  filter(NOMBRE == 'Intercuenca Alto Apurímac')
apu_geom <- Apurimac$geometry
# Creamos un buffer
buf_apu <- st_buffer(apu_geom,0.25)
# Intersectamos el buffer con las estaciones del SENAMHI
apu_stations <- st_intersection(data_sf,buf_apu)
# apurimac region 
apurimac_dataset <- datos_obs[apu_stations$id]
sp_apu = as(apu_stations,'Spatial') # sf a sp
# La transpuesta de la base de datos de lluvia de apurimac
ap_dataset = apurimac_dataset %>% t %>% tbl_df()
sp_apu@data = ap_dataset

library(gstat)
library(automap)
## Grilla
apurimac_sp = as(apu_geom,'Spatial')
grilla = makegrid(apurimac_sp,cellsize = 0.1)
mi_grilla = SpatialPoints(grilla)

#GEOESTADISTICA PARA ALTO APURIMAC
directory = '/home/aybarpc01/Downloads/shp/rainfall_apurimac/'

for (x in 1:452) {
  # 1. Definir
  monthly_rain = sp_apu[x]
  # 2. Cambiamos el nombre
  names(monthly_rain) = 'rain'
  # 3. Creamos el variograma
  variog = autofitVariogram(rain~1,monthly_rain)
  # 4. Creamos el variograma
  #projection(mi_grilla) = projection(monthly_rain)
  # 5. Definimos el kriging
  kr = krige(rain~1,monthly_rain,mi_grilla,model=variog$var_model)
  # 6. Pasamos de puntos a Raster
  estimaciones = kr[1]
  gridded(estimaciones) = T
  R_estim = raster(estimaciones)
  # 7. Guardar los resultados
  name_raster = sprintf("%s/Apurimac_Rain_%s.tif",
                        directory,
                        sq_date[x])
  writeRaster(R_estim,name_raster)
}

