import geopandas as gpd
import matplotlib.pyplot as plt
import fiona
import svgwrite
from shapely.ops import transform
from shapely.wkt import loads
from shapely.geometry import Polygon, LineString
import pandas as pd


# def create_svg_from_polygon(polygon, scale_factor=1., class_name=None):
def create_svg_from_polygon(polygon, class_name=None, id_number=None):
    if isinstance(polygon, Polygon):
        if polygon.is_empty:
            return '<g />'
        if class_name is None:
            class_name='default'
        exterior_coords = [
            ["{},-{}".format(*c) for c in polygon.exterior.coords]]
        interior_coords = [
            ["{},-{}".format(*c) for c in interior.coords]
            for interior in polygon.interiors]
        path = " ".join([
                            "M {} L {} z".format(coords[0], " L ".join(coords[1:]))
                            for coords in exterior_coords + interior_coords])
        if id_number is None:
            return (
                '<path fill-rule="evenodd" class="{1}" d="{0}" />'
            ).format(path, class_name)
        else:
            return (
                '<path fill-rule="evenodd" class="{1}" id="{2}" d="{0}" />'
            ).format(path, class_name, id_number)


def create_svg_from_linestring(linestring, scale_factor=1., stroke_color=None, class_name=None):
    if isinstance(linestring, LineString):
        if linestring.is_empty:
            return '<g />'
        if stroke_color is None:
            stroke_color = "#66cc99" if linestring.is_valid else "#ff3333"
        if class_name is None:
            class_name='default'
        pnt_format = " ".join(["{},-{}".format(*c) for c in linestring.coords])
        return (
            '<polyline fill="none" stroke="{2}" stroke-width="{1}" '
            'points="{0}" class="{3}" opacity="0.8" />'
        ).format(pnt_format, 2. * scale_factor, stroke_color, class_name)

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
# print(create_svg(parcel))
# print(parcel)
parcel_polygon = Polygon(parcel)
# print(parcel_polygon)
# print(transform(lambda x,y,z=None: (x, y*-1), parcel_polygon))
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
        if layer_name == 'GRASS' or layer_name == 'PARCELS' or layer_name == 'ROAD':
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
        text_rus = text.split(' ')[0]+' м2'
        points_text_area.append(text_rus)
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
parcels_id = gpd.sjoin(parcels_df, points_df_id, how='inner', op='intersects').drop(['index_right'], axis='columns')

parcels = gpd.sjoin(parcels_id, points_df_area, how='inner', op='intersects').drop(['index_right'], axis='columns')
# parcels_area = gpd.sjoin(parcels_id, points_df_area)
# print(parcels_id.drop_duplicates(subset=['id'], keep=False))
# print(parcels_area)

# print(parcels.head())

# for i in parcels_id.index:
#     print(parcels_id.loc[i].geometry)
# print(parcels_id.loc[160])

# print(union_obj)
# print(points_df)

# print(points_df)
# print(parcels_df)
# print(union_obj)

svg = list()

for layer in obj_list:
    if layer == 'ROAD':
        for obj in obj_list[layer]:
            svg.append(create_svg_from_polygon(obj, class_name='road'))

for layer in obj_list:
    if layer == 'GRASS':
        for obj in obj_list[layer]:
            svg.append(create_svg_from_polygon(obj, class_name='grass'))

for layer in obj_list:
    if layer == 'PARCELS':
        i=0
        for obj in obj_list[layer]:
            svg.append(create_svg_from_polygon(obj, class_name='parcels', id_number=i))
            i+=1 # TODO: Жуткий костыль!!

for layer in obj_list:
    if layer == 'AXIS':
        for obj in obj_list[layer]:
            svg.append(create_svg_from_linestring(obj, class_name='axis'))


# for layer in obj_list:
#     if layer != 'TEXT':
#         if layer == 'GRASS':
#             for obj in obj_list[layer]:
#                 svg.append(create_svg_from_polygon(obj, class_name='grass'))
#         elif layer == 'PARCELS':
#             for obj in obj_list[layer]:
#                 svg.append(create_svg_from_polygon(obj, class_name='parcels'))
#         elif layer == 'AXIS':
#             for obj in obj_list[layer]:
#                 svg.append(create_svg_from_linestring(obj, class_name='axis'))
                # svg.append(obj.svg())
    # else:
    #     for obj in obj_list[layer]:
    #         x = float(obj[0].x)
    #         y = float(obj[0].y)*-1
    #         text = """<text x="%s" y="%s">%s</text>""" %(x,y, obj[1])
    #         svg.append(text)

for i in parcels.index:
    centroidx = parcels.loc[i].geometry.centroid.x
    centroidy = parcels.loc[i].geometry.centroid.y*-1
    id = parcels.loc[i].id
    area = parcels.loc[i].area
    line = """<path class="line" d="M%s %s L %s %s"/>""" %(centroidx-5,centroidy, centroidx+5, centroidy)
    text_id = """<text class="text-id" x="%s" y="%s" >%s</text>""" %(centroidx-5,centroidy-2, id)
    text_area = """<text class="text-area" x="%s" y="%s" >%s</text>""" %(centroidx-5,centroidy+5, area)
    svg.append(line)
    svg.append(text_id)
    svg.append(text_area)

# viewBox="1382800 493250 900 500"
# viewBox="1381940 492750 800 450"
# viewBox="1381935 -493220 800 450"
# < svg
# version = "1.1"
# viewBox = "1381935 -493220 3850 1950"
# baseProfile = "full"
# xmlns = "http://www.w3.org/2000/svg"
# xmlns:xlink = "http://www.w3.org/1999/xlink"
# xmlns:ev = "http://www.w3.org/2001/xml-events"
# width = "400%"
# height = "400%" >

svg_header = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>DXF to SVG converter</title>
    <style>
        .road{
            stroke-width: 0.2px;
            fill: #e1e1eb;
        }

        .parcels{
            stroke: #2ee3ba;
            stroke-width: 0.2px;
            fill: #ffffeb;
        }

        .grass{
            stroke: #8a966e;
            stroke-width: 0.2px;
            fill: #b3e3ba;
        }

        .axis{
            stroke: #696a69;
            stroke-dasharray: 2;
            fill: none;
            stroke-width: 0.2px;
        }

        .text-id{
            font-size: 5px;
        }

        .text-area{
            font-size: 3px;
        }

        .line{
            stroke: #000000;
            fill: none;
            stroke-width: 0.2px;
        }
    </style>
</head>
<body>
    <svg version="1.1"
     viewBox="1381935 -493220 1500 1000"
     baseProfile="full"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:ev="http://www.w3.org/2001/xml-events"
     width="1500" height="1000">
     <g>
"""

svg_footer = """\n</g>
</svg>
<script src="https://d3js.org/d3.v4.min.js"></script>
<script>

var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var g = svg.selectAll("g")

svg.append("rect")
    .attr("fill", "none")
    .attr("x", "1381935")
    .attr("y", "-493220")
    .attr("pointer-events", "all")
    .attr("width", width)
    .attr("height", height)
    .attr("style", "stroke:black")
    .call(d3.zoom()
        .scaleExtent([1, 8])
        .on("zoom", zoom));

function zoom() {
  g.attr("transform", d3.event.transform);
}

</script>
</body>
</html>
"""

file = open('index.html', 'w')
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