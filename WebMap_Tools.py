import json,requests,arcgis, os
from fiona import open as fopen
from fiona.crs import from_epsg

class WebMap_Tools:
    def __init__(self,
                 webmap,
                 username,
                 password,
                 portal_url=None
                 ):
        self.conn = arcgis.gis.GIS(portal_url, username, password)
        self.wm = self.get_map(webmap)
        #self.geojson=self.process(map_name)

    def get_map(self, map_name):
        wm_item = self.search_item(map_name, 'Web Map')
        wm = arcgis.mapping.WebMap(wm_item)
        return wm

    def disable_popups(self):
        wm_data = self.wm.definition
        for layer in wm_data['operationalLayers']:
            layer['disablePopup'] = True
        item_properties = {"text": wm_data}
        self.wm.update(item_properties=item_properties)
        print("Pop-ups disabled")

    def list_map_layer_defs(self):
        layer_defs = []
        for layer in self.wm.layers:
            layer_defs.append(layer)
        return layer_defs

    """
    Returns a list of dictionaries. Each dictionary contains the Web Map layer name and its corresponding GeoJSON.
    Optionally, writes layers to geojson (.json) files
    """
    
    def map_to_geojson(self, geojson=False, shp=False, out_folder=None):
        gj_list = []
        for layer in self.wm.layers:
            try:
                fc = arcgis.features.FeatureLayer(layer["url"],gis=self.conn)
                srs = fc.properties["extent"]["spatialReference"]["latestWkid"]
                data = json.loads(fc.query().to_geojson)
                data.update({"crs":{"type":"name","properties":{"name":"EPSG:%s" % srs}}})
                geojson_dict = {"name": layer["title"], "geojson": data}
                gj_list.append(geojson_dict)
                if out_folder is not None:
                    if geojson is True:
                        self.geojson_to_file(out_folder, geojson_dict)
                    if shp is True:
                        self.geojson_to_shp(out_folder, geojson_dict, srs)
            except Exception as e:
                return e
        return gj_list

        
    def geojson_to_shp(self, out_folder, geojson_dict, srs):
        try:
            code = from_epsg(srs)
            b_json = json.dumps(geojson_dict['geojson']).encode('utf-8')
            geojson = fiona.ogrext.buffer_to_virtual_file(b_json)
            file_name = self.char_replace(geojson_dict["name"]) + ".shp"
            out_path = os.path.join(out_folder, file_name)
            with fopen(geojson) as source:
                with fopen(
                        out_path,
                        "w",
                        driver="ESRI Shapefile",
                        crs = code,
                        schema=source.schema) as sink:
                    for rec in source:
                        sink.write(rec)
            print("Shapefile written to %s " % out_path)   
        except Exception as e:
            print(e)
        return

    def geojson_to_file(self, out_folder, geojson_dict):
        try:
            file_name = self.char_replace(geojson_dict['name']) + '.json'
            out_path = os.path.join(out_folder, file_name)
            with open(out_path, 'w') as outfile:
                json.dump(geojson_dict['geojson'], outfile)
            print("GeoJSON written to %s " % out_path)
        except Exception as e:
            print(e)


    def search_item(self, item_name, item_type, flc=False):
        search_results = self.conn.content.search(item_name, item_type=item_type)
        proper_index = [i for i, s in enumerate(search_results) if '"' + item_name + '"' in str(s)]
        found_item = search_results[proper_index[0]]
        if flc == False:
            get_item = self.conn.content.get(found_item.id)
            return get_item
        if flc == True:
            flc = FeatureLayerCollection.fromitem(found_item)
            return flc

    def char_replace(self, name):
        special = ['.',',','<','>',
                   '/','?',':',';',
                   "'",'"','[',']',
                   '{','}','|','\\',
                   '+','=','-',')',
                   '(','*','&','^',
                   '%','$','#','@',
                   '!','~','`']

        for ele in special:
            if ele in name:
                name = name.replace(ele,'_')
        return name    
    
    def update_wm_layer(self):
        item_data = item.get_data()

        print("**************************ORIGINAL DEFINITION******************************")
        print(json.dumps(item_data, indent=4, sort_keys=True))
        # Open JSON file containing symbology update
        with open('/root/webmaplyr.json') as json_data:
            data = json.load(json_data)

        # Set the item_properties to include the desired update
        item_properties = {"text": json.dumps(data)}

        # 'Commit' the updates to the Item
        item.update(item_properties=item_properties)

        # Print item_data to see that changes are reflected
        # item_data = item.get_data()
        print("*******************************NEW DEFINITION******************************")
        print(json.dumps(item_data, indent=4, sort_keys=True))