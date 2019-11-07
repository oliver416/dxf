import geopandas as gpd
import pandas as pd
from shapely.wkt import loads
from shapely.geometry import Polygon, LineString
from ..models import Parcel


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


def read_dxf(file_path, result_path):
    dxf = gpd.read_file(file_path)

    obj_list = {}
    for layer in set(dxf['Layer']):
        obj_list[layer] = list()

    for item in dxf.index:
        layer_name = dxf.loc[item]['Layer']
        if layer_name:
            if layer_name == 'GRASS' or layer_name == 'PARCELS' or layer_name == 'ROAD':
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

    parcels_gs = gpd.GeoSeries(obj_list['PARCELS'])
    parcels_df = gpd.GeoDataFrame({'geometry': parcels_gs})

    text_geometry_array = list()
    text_geometry_text = list()
    for text in obj_list['TEXT']:
        text_geometry_array.append(text[0])
        text_geometry_text.append(text[1])

    points_gs_geometry = gpd.GeoSeries(text_geometry_array)
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

    parcels_id = gpd.sjoin(parcels_df, points_df_id, how='inner', op='intersects').drop(['index_right'], axis='columns')

    parcels_area = gpd.sjoin(parcels_id, points_df_area, how='inner', op='intersects').drop(['index_right'], axis='columns')

    parcels = pd.merge(parcels_id, parcels_area, on='id', how='outer').drop(['geometry_y'], axis='columns').rename(columns={'geometry_x': 'geometry'})

    parcel_data = dict()

    for parcel in Parcel.objects.all():
        pid = parcel.parcel_id
        area = parcel.area
        status = parcel.status
        price = parcel.price
        parcel_data[pid] = dict()
        parcel_data[pid]['area'] = area
        parcel_data[pid]['status'] = status
        parcel_data[pid]['price'] = price

    # for parcel in parcels.index:
    #     pid = parcels.loc[parcel].id
    #     area = parcels.loc[parcel].area
    #     parcel_data[pid] = dict()
    #     parcel_data[pid]['area'] = area
    #     if isinstance(area, str):
    #         parcel_data[pid]['saled'] = False
    #     else:
    #         parcel_data[pid]['saled'] = True

    svg = list() #TODO: choose layers

    for layer in obj_list:
        if layer == 'ROAD':
            for obj in obj_list[layer]:
                svg.append(create_svg_from_polygon(obj, class_name='road'))

    for layer in obj_list:
        if layer == 'GRASS':
            for obj in obj_list[layer]:
                svg.append(create_svg_from_polygon(obj, class_name='grass'))

    for i in parcels.index:
        area = parcels.loc[i].area
        if isinstance(area, str):
            svg.append(create_svg_from_polygon(parcels_id.loc[i].geometry, class_name='parcels parcels-free', id_number=parcels_id.loc[i].id))
        else:
            svg.append(create_svg_from_polygon(parcels_id.loc[i].geometry, class_name='parcels parcels-sold', id_number=parcels_id.loc[i].id))

    for layer in obj_list:
        if layer == 'AXIS':
            for obj in obj_list[layer]:
                svg.append(create_svg_from_linestring(obj, class_name='axis'))


    for i in parcels.index:
        centroidx = parcels.loc[i].geometry.centroid.x
        centroidy = parcels.loc[i].geometry.centroid.y*-1
        id = parcels.loc[i].id
        area = parcels.loc[i].area
        line = """<path class="line" d="M%s %s L %s %s"/>""" %(centroidx-5,centroidy, centroidx+5, centroidy)
        text_id = """<text class="text-id" x="%s" y="%s" >%s</text>""" %(centroidx-5,centroidy-2, id)
        text_area = """<text class="text-area" x="%s" y="%s" >%s</text>""" %(centroidx-5,centroidy+5, area)
        if isinstance(area, str):
            svg.append(line)
            svg.append(text_area)
        svg.append(text_id)

    # TODO: magic viewbox
    # TODO: svg header
    # TODO: download d3 js
    # TODO: render dxf after xls

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
            }

            .parcels-sold{
                fill: #fee6e9;
            }

            .parcels-free{
                fill: #ffffeb;
            }

            .parcels-booked{
                fill: #9c9c95;
            }

            .parcels:hover{
                fill: rgba(55,55,55,0.4);
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
                cursor: default;
            }

            .text-area{
                font-size: 3px;
                cursor: default;
            }

            .line{
                stroke: #000000;
                fill: none;
                stroke-width: 0.2px;
            }

            .onpopup{
                width: 100px;
                height: 100px;
                background-color: red;
                position: relative;
                width: 120px;
                background-color: #fff;
                border: 1px solid #ccc;
                font-family: sans-serif;
                font-size: 16px;
                padding: 10px;
                padding-left: 10px;
                padding-left: 15px;
                border-radius: 10px;
                z-index: 1;
                max-height: 130px;
                overflow: hidden;
                background-color:
                #d7d7e1;
                border: 2px solid
                #3283ba;
                border-radius: 10px;
                font-weight: 500;
                text-align: left;
            }

            .onpopup .sold{
                color: #e82100;
            }

            .onpopup .free{
                color: #008000;
            }

            .onpopup .booked{
                color: #851194;
            }

            svg{
                border-style: solid;
                border-color: black;
                border-width: 1px;
                position: absolute;
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
    <div id="popup"></div>
    <script src="https://d3js.org/d3.v4.min.js"></script>
    <script>

    let svg = d3.select("svg"),
        width = +svg.attr("width"),
        height = +svg.attr("height");

    let g = svg.selectAll("g")

    svg.call(d3.zoom()
            .scaleExtent([1, 8])
            .on("zoom", zoom));

    function zoom() {
      g.attr("transform", d3.event.transform);
    }

    let parcels = document.querySelectorAll('.parcels').forEach(
        function(item){
            item.addEventListener('mouseenter', onMouseEnter);
            item.addEventListener('mouseleave', onMouseLeave);
        }
    );

    let popup = document.getElementById("popup");

    const nan = NaN;
    const True = true;
    const False = false;
    let parcel_data = %s;

    function onMouseEnter(e){
        let id = e.target.id;
        let area = parcel_data[id]['area'];
        let status = parcel_data[id]['status'];
        let price = parcel_data[id]['price'];

        popup.classList.add("onpopup");

        switch(status){
            case 'Sold':
                popup.innerHTML='Участок №'+id+'<br>'+area+' м<sup>2</sup><br>'+price+'<br>'+'<span class="sold">Продан</span>';
                break
            case 'Free':
                popup.innerHTML='Участок №'+id+'<br>'+area+' м<sup>2</sup><br>'+price+'<br>'+'<span class="free">Свободен</span>';
                break
            case 'Booked':
                popup.innerHTML='Участок №'+id+'<br>'+area+' м<sup>2</sup><br>'+price+'<br>'+'<span class="booked">Забронирован</span>';
                break
        }

        popup.style.left=e.pageX+"px";
        popup.style.top=e.pageY+"px";
    }

    function onMouseLeave(e){
        popup.classList.remove("onpopup");
        popup.innerText='';
    }

    </script>
    </body>
    </html>
    """ % parcel_data

    file = open(result_path, 'w')
    file.write(svg_header)
    for i in svg:
        file.write(i+'\n')
    file.write(svg_footer)
    file.close()

    return
