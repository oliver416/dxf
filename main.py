import geopandas as gpd
import matplotlib.pyplot as plt
import fiona
import svgwrite
from shapely.wkt import loads
from shapely.geometry import Polygon
import pandas as pd

# print(gpd.__version__)
# print(fiona.supported_drivers)
dxf = gpd.read_file('./data/For_svg.dxf')
# print(dxf)
# print(dxf.loc[840].geometry)
# p = loads(str(dxf.loc[840].geometry))
# print(p.envelope)
# print(p.is_ring)
# poly = Polygon(p)
# print(poly)
# print(poly.centroid)
# print(dxf.loc[0]['Layer'])

parcel = loads(str(dxf.loc[400].geometry))
parcel_polygon = Polygon(parcel)
parcel_polygon = gpd.GeoSeries(parcel_polygon)
parcel_polygon = gpd.GeoDataFrame({'geometry': parcel_polygon})

parcel_centroid = parcel_polygon.centroid
temp = parcel_centroid
parcel_centroid = parcel_centroid.buffer(1)
parcel_centroid = gpd.GeoSeries(parcel_centroid)
parcel_centroid = gpd.GeoDataFrame({'geometry': parcel_centroid, 'text': 'wow'})

# print('TEMP ', float(temp.x))

# print(gpd.sjoin(parcel_polygon, parcel_centroid).loc[0].geometry)
# print(gpd.sjoin(parcel_polygon, parcel_centroid))

# column names
# print(type(dxf.columns))

# list of layers
# print(set(dxf['Layer']))

obj_list = {}
for layer in set(dxf['Layer']):
    obj_list[layer] = list()

for item in dxf.index:
    layer_name = dxf.loc[item]['Layer']
    if layer_name:
        if layer_name == 'GRASS' or layer_name == 'PARCELS':
        # if layer_name == 'GRASS':
            obj = loads(str(dxf.loc[item].geometry))
            obj = Polygon(obj)
            obj_list[layer_name].append(obj)
        elif layer_name ==  'TEXT':
            obj = loads(str(dxf.loc[item].geometry))
            text = dxf.loc[item]['Text']
            obj_list[layer_name].append([obj, text])
        else:
            obj = loads(str(dxf.loc[item].geometry))
            obj_list[layer_name].append(obj)

# for parcel in obj_list['PARCELS']:
#     print(parcel)

parcels_gs = gpd.GeoSeries(obj_list['PARCELS'])
parcels_df = gpd.GeoDataFrame({'geometry': parcels_gs})

text_geometry_array = list()
text_geometry_text = list()
for text in obj_list['TEXT']:
    # point = text[0]
    # buffer = point.buffer(0.1)
    text_geometry_array.append(text[0])
    text_geometry_text.append(text[1])

points_gs_geometry = gpd.GeoSeries(text_geometry_array)
# points_gs_text = gpd.GeoSeries(text_geometry_text)
points_gs_text = pd.Series(text_geometry_text)
points_df = gpd.GeoDataFrame({'geometry': points_gs_geometry, 'text': points_gs_text})

points_geometry_id = list()
points_text_id = list()
points_geometry_area = list()
points_text_area = list()
for item in points_df.index:
    text = points_df.loc[item].text
    geometry = points_df.loc[item].geometry
    if len(text) > 4:
        points_geometry_area.append(geometry)
        points_text_area.append(text)
    else:
        points_geometry_id.append(geometry)
        points_text_id.append(text)

points_gs_id = gpd.GeoSeries(points_geometry_id)
points_gs_id_text = pd.Series(points_text_id)
points_df_id = gpd.GeoDataFrame({'geometry': points_gs_id, 'id': points_gs_id_text})

points_gs_area = gpd.GeoSeries(points_geometry_area)
points_gs_area_text = pd.Series(points_text_area)
points_df_area = gpd.GeoDataFrame({'geometry': points_gs_area, 'area': points_gs_area_text})

# union_obj = gpd.overlay(parcels_df, points_df, how='union')
# parcels_id = gpd.sjoin(parcels_df, points_df_id).drop(['index_right'], axis='columns')
parcels_id = gpd.sjoin(parcels_df, points_df_id, how='inner', op='intersects')
# parcels_area = gpd.sjoin(parcels_id, points_df_area)
print(parcels_id.drop_duplicates(subset=['id'], keep=False))
# print(parcels_area)

for i in parcels_id.index:
    print(parcels_id.loc[i].geometry)
print(parcels_id.loc[105])

# print(union_obj)
# print(points_df)

# print(points_df)
# print(parcels_df)
# print(union_obj)

svg = list()
for layer in obj_list:
    if layer != 'TEXT':
        if layer == 'PARCELS':
            pass
            # for obj in parcels_area:
            #     print(obj)
        else:
            for obj in obj_list[layer]:
                svg.append(obj.svg())
    else:
        for obj in obj_list[layer]:
            # geometry = obj[0]
            x = float(obj[0].x)
            y = float(obj[0].y)
            text = """<text x="%s" y="%s">%s</text>""" %(x,y, obj[1])
            svg.append(text)

# viewBox="1382800 493250 900 500"
# transform="rotate(180)"

svg_header = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
    "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1"
     viewBox="1381940 492750 800 450"
     baseProfile="full"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:ev="http://www.w3.org/2001/xml-events"
     width="100%" height="100%">

"""

svg_footer = """\n</svg>"""

file = open('001.svg', 'w')
file.write(svg_header)
for i in svg:
    file.write(i+'\n')
file.write(svg_footer)
file.close()


# for i in obj_list:
#     print(i.svg())

    # obj = loads(str(dxf.loc[item].geometry))
    # if obj.is_ring:


# It works
# print(dxf.loc[980].geometry.svg())
# p = loads(str(dxf.loc[980].geometry))
# q = dxf.loc[980]
# print(p.svg())
# print(dxf.to_json())

# It works
# dwg = svgwrite.Drawing('test.svg', profile='tiny')
# dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
# dwg.add(dwg.text('Test', insert=(0, 0.2), fill='red'))
# dwg.save()

# перебрать геометрию
# for i in dxf.index:
#     print(dxf.loc[i].geometry.svg())

# работает
# dxf.to_file('1.tab', driver='MapInfo File')
# dxf.to_file('2.shp', driver='ESRI Shapefile')

# print(dxf.loc[3].geometry)
# print(dxf.loc[3])
# dxf.plot()

# matplotlib example
# fig = plt.figure()
# plt.scatter(1.0, 1.0)
# plt.show()