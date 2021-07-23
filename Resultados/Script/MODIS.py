#!/usr/bin/env python
# coding: utf-8

# ## Inicializando Google Earth Engine

# In[1]:


import ee # # Authenticates and initializes Earth Engine
import geemap # A dynamic module of Google Earth Engine
import fiona # For geopackage file handling 
import os #To set and modify filepaths
import json # For json objects
import urllib # For download geopackage files


# In[2]:


def ee_initialize(): ## Initializing in Google Earth Engine as function
    try:
        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()
ee_initialize()


# In[3]:


Map= geemap.Map(center=[-12,-75],zoom=5)
Map.add_basemap('SATELLITE')


# ## Conviertiendo geopackage a geojson

# In[4]:


def is_url(url): # URL Input verification
    """Check to see if *url* has a valid protocol."""
    import urllib 
    try:
        return urllib.parse.urlparse(url).scheme in ('http', 'https') 
    except Exception:
        return False


# In[5]:


def gpkg_to_geojson(in_gpkg, layer= None, out_json=None):
    """Converts specific layer from geopackage file to GeoJSON.
    Args:
        in_gpkg (str): File path or URL of geopackage file.
        layer (str, optional): Layer name or number of the geopackage file. Defaults first layer as None
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.
    Returns:
        object: The json object representing the geopackage layer.
    """   
    ee_initialize()
    try: 
        import fiona
        import json  
        if os.path.exists(in_gpkg): # If the path is a filepath      
                path_or_bytes = os.path.abspath(in_gpkg)
                reader = fiona.open
                if out_json is None:  ## Obtaining empty output json
                    out_json = os.path.splitext(in_gpkg)[0] + ".json"
                elif os.path.exists(out_json): # If the out_json is duplicated
                    out_json = out_json.replace('.json', '_bk.json')  
                elif not os.path.exists(os.path.dirname(out_json)): # If the filepath has not been created yet
                    os.makedirs(os.path.dirname(out_json))    
      
                    
        elif is_url(in_gpkg): # If the path is a URL                  
                path_or_bytes = urllib.request.urlopen(in_gpkg).read()
                reader = fiona.BytesCollection            
                if out_json is None: # If the ouput name of the json is not specified
                    out_json = os.path.split(in_gpkg)[1].split(".")[0] + ".json"
                elif os.path.exists(out_json): # If the out_json is duplicated
                    out_json = out_json.replace('.json', '_bk.json')    
                elif not os.path.exists(os.path.dirname(out_json)): # If the filepath has not been created yet
                    os.makedirs(os.path.dirname(out_json))             

        buffer=[]         
        with reader(path_or_bytes, layer = layer, enabled_drivers="GPKG") as features:
            for feature in features: #Reading each feature of geopackage we obtain a dict keys for json
                    ids = feature["id"]
                    atr = feature["properties"]
                    geom = feature["geometry"]
                    buffer.append(dict(type="Feature", id = ids, geometry=geom, properties=atr)) 

        with open(out_json, "w") as geojson: 
            geojson.write(json.dumps({"type": "FeatureCollection", #Writing in a json our buffer list
                                 "features":buffer}, indent=2))
            geojson.close()          
        with open(out_json) as f:
             json_data = json.load(f) #Reading a full json and return it as result
       
        return json_data

    except Exception as e:
        print(e)


# In[6]:


def gpkg_to_ee(in_gpkg, layer=None):
    """Converts specific layer from geopackage file to  Earth Engine object.
    Args:
        in_gpkg (str): File path or URL of geopackage file.
        layer (str, optional): Layer name or number of the geopackage. Defaults first layer as None
        
    Returns:
        object: Earth Engine objects representing the geopackage layer.
    """
    ee_initialize()
    try:
        json_data = gpkg_to_geojson(in_gpkg, layer= layer) ## Converting geopackage file to geojson
        ee_object  = geemap.geojson_to_ee(json_data) ## Converting geojson to ee object
        return ee_object
    except Exception as e:
        print(e) 


# ##  Descargando coleccion de imagenes MODIS13Q1

# In[7]:


## Vector data from filepath
workspace = r"C:\Users\51937\Desktop\UNMSM\CICLO VII\TELEDETECCIÓN\Fires\Materiales"
geegpkg = os.path.join(workspace,"Anta.gpkg")

## Creating a ee.FeatureCollection
anta_ee= gpkg_to_ee(geegpkg,layer="Anta")
anta_ee


# In[9]:


def clipped(image):
    return image.clip(anta_ee)


# In[10]:


modis_dataset= ee.ImageCollection("MODIS/006/MOD13Q1").select('NDVI')      .filter(ee.Filter.date('2016-01-01', '2016-12-31'))      .map(clipped)
ndvi = {
  "min": 0.0,
  "max": 8000.0,
  "palette": [
    'FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901',
    '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01',
    '012E01', '011D01', '011301'
  ],
}

Map.addLayer(modis_dataset, ndvi, 'NDVI')
Map


# In[11]:


out_dir = r"C:\Users\51937\Desktop\UNMSM\CICLO VII\TELEDETECCIÓN\Fires\Resultados\NDVI"
count = int(modis_dataset.size().getInfo())
images = modis_dataset.toList(count)  

## Para conocer los nombres de las bandas de una imagen MODIS
image_1 = ee.Image(images.get(0))
print("La banda utilizada es el {} para un producto MODIS con {} imagenes"      .format(image_1.get('system:band_names').getInfo()[0],count))


# In[12]:


for i in range(0, count):
    image = ee.Image(images.get(i))
    start = ee.Date(image.get("system:time_start")).format('YYYY-MM-dd').getInfo() 
    end = ee.Date(image.get("system:time_end")).format('YYYY-MM-dd').getInfo()
    filename= "MOD13Q1_NDVI_250m_16_days" + "_" + "{}".format(start) +"_" +"{}".format(end) + ".tif"
    filepath = os.path.join(out_dir,filename)
    geemap.ee_export_image(image, filename= filepath, scale=30,
                           region=anta_ee.geometry(), file_per_band=False)


# In[ ]:




