import geopandas as gpd
import pandas as pd
from math import ceil
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

    bounds = dxf.total_bounds
    boundx = ceil(bounds[0])
    boundy = ceil(bounds[3])

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

        points_geometry_id.append(geometry)
        points_text_id.append(text)

        points_text_area.append(str(Parcel.objects.get(parcel_id=int(text)).area))
        points_geometry_area.append(geometry)

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

    svg = list()

    for layer in obj_list:
        if layer == 'ROAD':
            for obj in obj_list[layer]:
                svg.append(create_svg_from_polygon(obj, class_name='road'))

    for layer in obj_list:
        if layer == 'GRASS':
            for obj in obj_list[layer]:
                svg.append(create_svg_from_polygon(obj, class_name='grass'))

    for i in parcels.index:
        pid = int(parcels_id.loc[i].id)
        if parcel_data[pid]['status'] == 'Free':
            svg.append(create_svg_from_polygon(parcels_id.loc[i].geometry, class_name='parcels parcels-free', id_number=parcels_id.loc[i].id))
        elif parcel_data[pid]['status'] == 'Sold':
            svg.append(create_svg_from_polygon(parcels_id.loc[i].geometry, class_name='parcels parcels-sold', id_number=parcels_id.loc[i].id))
        else:
            svg.append(create_svg_from_polygon(parcels_id.loc[i].geometry, class_name='parcels parcels-booked', id_number=parcels_id.loc[i].id))

    for layer in obj_list:
        if layer == 'AXIS':
            for obj in obj_list[layer]:
                svg.append(create_svg_from_linestring(obj, class_name='axis'))


    for i in parcels.index:
        centroidx = parcels.loc[i].geometry.centroid.x
        centroidy = parcels.loc[i].geometry.centroid.y*-1
        id = parcels.loc[i].id
        area = int(parcel_data[int(id)]['area'])
        line = """<path class="line" d="M%s %s L %s %s"/>""" %(centroidx-5,centroidy, centroidx+5, centroidy)
        text_id = """<text class="text-id" x="%s" y="%s" >%s</text>""" %(centroidx-5,centroidy-2, id)
        text_area = """<text class="text-area" x="%s" y="%s" >%s м<tspan class="square" dy ="-1">2</tspan></text>""" %(centroidx-5,centroidy+5, area)
        svg.append(line)
        svg.append(text_area)
        svg.append(text_id)

    svg_header = """<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>Земельные участки</title>
        <style>
            body {
                margin: 0;
            }

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
                fill: #ffe300;
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

            .square{
                font-size: 2px;
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
                position: absolute;
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
                box-sizing: unset;
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
                width: 100%%;
                background-color: #eeeeee;
            }

            section {
                width: 100%%;
            }
        </style>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
        <!--jquery-->
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.0/jquery.min.js"></script>
        <script src="http://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
        <!--js-libs-->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.19.1/jquery.validate.js"></script>
        <!--fontawesome-->
        <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.0.13/css/all.css" integrity="sha384-DNOHZ68U8hZfKXOrtjWvjxusGo9WQnrNx2sqG0tfsghAvtVlRW3tvkXWZh58N9jp" crossorigin="anonymous">
        <!--my js-->
        <script src="https://d3js.org/d3.v4.min.js"></script>
    </head>
    <body>
        <svg version="1.1"
         viewBox="%s -%s 770 400">
         <g>
    """ % (str(boundx), str(boundy))

    svg_footer = """\n</g>
    </svg>
    <div id="popup"></div>

    <section class="calculation">
            <div class="container">
                <div class="row">

                    <div class="col-12 d-flex justify-content-center">
                        <form action="submit" class="calculator d-flex" id="credit-calc-form" style="margin: 30px auto;">
                          <div class="row justify-content-center">
                            <div class="col-12 col-md-8 d-flex justify-content-between p-0">

                             <div class="row p-0">

                                <div class="col-12">
                                 <div class="form-group">
                                  <div class="input-group input-group-lg">
                                   <!-- <label>Номер участка</label> -->
                                  <div class="input-group-prepend">
                                    <span class="input-group-text">Номер участка</span>
                                  </div>
                                   <select class="form-control" id="plot-select">
                                       <option disabled selected="selected">Выберите участок</option>
                                   </select>
                                  </div>
                                 </div>
                               </div>

                              <div class="col-12 col-lg-6">
                                <div class="form-group">
                                  <div class="input-group input-group-lg">
                                  <!-- <label>Срок кредита</label> -->
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">Срок кредита</span>
                                    </div>
                                    <select class="form-control" id="years-select">
                                        <option>Нет</option>
                                        <option>1 год</option>
                                        <option>2 года</option>
                                        <option>3 года</option>
                                        <option>5 лет</option>
                                    </select>
                                  </div>
                                  </div>
                              </div>

                              <div class="col-12 col-lg-6">
                               <div class="form-group">
                                <div class="input-group input-group-lg">
                                 <!-- <label for="formGroupExampleInput">Первый взнос, &#8381; (мин. 10%%)</label> -->
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">Первый взнос, &#8381</span>
                                    </div>
                                 <input type="text" class="calc__invest calc__start-invest form-control" id="invest-input" name="invest-input">
                                </div>
                               </div>
                            </div>

                             </div>

                            </div>

                          <div class="row justify-content-md-center">

                            <div class="col-12 col-md-8 col-lg-5 d-flex flex-column">
                              <div class="form-group">
                                <div class="input-group input-group-lg">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">Площадь, м&#178;</span>
                                    </div>
                                    <input disabled class="form-control" name="area-input" id="area-input">
                                </div>
                              </div>
                              <div class="form-group">
                                <div class="input-group input-group-lg">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">Стоимость, &#8381;</span>
                                    </div>
                                    <input disabled class="form-control" name="price-area" id="price-input">
                                </div>
                              </div>
                            </div>

                            <div class="col-12 col-md-8 col-lg-5 d-flex flex-column">
                              <div class="form-group">
                                <div class="input-group input-group-lg">
                                  <div class="input-group-prepend">
                                    <span class="input-group-text">Стоимость с %%</span>
                                  </div>
                                  <input disabled class="form-control" name="price-area-perc-calc">
                                </div>
                              </div>
                              <div class="form-group">
                                <div class="input-group input-group-lg">
                                  <div class="input-group-prepend">
                                      <span class="input-group-text">Ежемесячно</span>
                                  </div>
                                  <input disabled class="form-control" name="invest-calc">
                                </div>
                              </div>
                            </div>



                              <div class="col-md-4 d-none">
                                  <div class="input-group input-group-lg d-none">
                                      <div class="input-group-prepend">
                                          <span class="input-group-text">Остаток</span>
                                      </div>
                                      <input disabled class="form-control" name="residue-calc">
                                  </div>
                                  <div class="input-group input-group-lg d-none">
                                      <div class="input-group-prepend">
                                          <span class="input-group-text">Наценка</span>
                                      </div>
                                      <input disabled class="form-control" name="markup-calc">
                                  </div>
                                  <div class="form-group  flex-column d-none" id="years-fields">
                                      <label for="formGroupExampleInput" class="mt-2 text-center" style="font-size: 24px;">Ставка</label>
                                      <div class="wrap d-flex flex-row">
                                          <div class="input-group input-group-sm mb-3 flex-column m-0">
                                              <div class="input-group-prepend">
                                                  <span class="input-group-text justify-content-center" style="width: 100%%;">1 год</span>
                                              </div>
                                              <input disabled class="form-control text-center" style="width: 100%%;" name="1">
                                          </div>
                                          <div class="input-group input-group-sm mb-3 flex-column m-0">
                                              <div class="input-group-prepend">
                                                  <span class="input-group-text justify-content-center" style="width: 100%%;">2 года</span>
                                              </div>
                                              <input disabled class="form-control text-center" style="width: 100%%;" name="2">
                                          </div>
                                          <div class="input-group input-group-sm mb-3 flex-column m-0">
                                              <div class="input-group-prepend">
                                                  <span class="input-group-text justify-content-center" style="width: 100%%;">3 года</span>
                                              </div>
                                              <input disabled class="form-control text-center" style="width: 100%%;" name="3">
                                          </div>
                                          <div class="input-group input-group-sm mb-3 flex-column m-0">
                                              <div class="input-group-prepend">
                                                  <span class="input-group-text justify-content-center" style="width: 100%%;">5 лет</span>
                                              </div>
                                              <input disabled class="form-control text-center" style="width: 100%%;" name="5">
                                          </div>
                                      </div>
                                  </div>
                              </div>

                              <div class="col-md-6 d-flex flex-column justify-content-center">
                                <button type="submit" class="btn btn-primary" id="costing-btn" style="margin: 15px auto;">Рассчитать</button>
                              </div>

                            </div>
                          </div>
                        </form>
                    </div>
                </div>
            </div>
        </section>

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

        popup.style.left=e.pageX+20+"px";
        popup.style.top=e.pageY+20+"px";
    }

    function onMouseLeave(e){
        popup.classList.remove("onpopup");
        popup.innerText='';
    }

    </script>
    <script>
      //Стоимость за кв.м.


      //массив с информацией по всем участкам
      //номер участка свопадает с внутренним номером начинающимся на "p"
      //первое значение - статус и окрас участка, цифра определяет присваиваемый класс:
      //по умолчанию стоит - 0 - (продан)  sold
      //второе значени площадь м2
      //третье значение цена
      //четвертое значение дополнительная строка
      // 1 - участок продан
      // 2 - участок свободен

      let myPlots = {};

      for (let i=1; i < Object.keys(parcel_data).length+1; i++){
            if (parcel_data[i]['status'] === 'Free'){
                myPlots['p'+i]='1|'+parcel_data[i]['area']+'|'+parcel_data[i]['price'];
            } else{
                myPlots['p'+i]='0|'+parcel_data[i]['area']+'|';
            }
      }


    //   var total_plots = 227 // TODO: change variable
      var total_plots = Object.keys(parcel_data).length
      window.onload = function() {
        FirstOutPutData();
        var myCollection = document.getElementsByClassName('dad-upper-cell');
        for(var i=0; i<myCollection.length; i++){
          myCollection[i].addEventListener("mouseover", function(){
            var x = this.id;
            x = x.slice( 1 );
            ShowInfoWin(x);
          });
          myCollection[i].addEventListener("mouseout", function(){
            HideInfoWin();
          })
        }
      };
      function FirstOutPutData(){
        for(var i=1; i<total_plots; i++){
        //   var myElem = document.getElementById('dp'+i);
          var myElem = document.getElementById(i);
          var myStr= 'p'+i;
          var CurrentDataArray = myPlots[myStr];
          CurrentDataArray = CurrentDataArray.split('|');
          if(CurrentDataArray[0]!=0){
            myElem.classList.remove('sold');
            myElem.classList.add('free');
          }
        }
      }
      function ShowInfoWin(x){
        var myStr= 'p'+x;
        var CurrentDataArray = myPlots[myStr];
        CurrentDataArray = CurrentDataArray.split('|');

        var myElem = document.getElementById('p'+x);
        var myObj = myElem.getBoundingClientRect();
        var myX = myObj.left;
        var myY = myObj.top;

        myElem = document.getElementById('dad-info-panel');
        myElem.style.display='block';
        myElem.style.left =  myX + -100 + 'px';
        myElem.style.top = myY - 120  +'px';

        var myElem = document.getElementById('dad-info-panel');
        myElem.style.display='block';

        var data0 = CurrentDataArray[0];
        var data1 = CurrentDataArray[1];
        var data2 = CurrentDataArray[2];
        myElem = document.getElementById('num-of-plots');
        myElem.innerHTML = 'Участок №' + x;
        if(data0==0){
          myElem = document.getElementById('data-status');
          myElem.innerHTML = 'ПРОДАН';
          if(myElem.classList.contains('green-font')){
            myElem.classList.remove('green-font');
            myElem.classList.add('red-font');
          }
          myElem.classList.add('red-font');

          myElem = document.getElementById('data-area');
          myElem.innerHTML = data1 + ' м&#178';
          myElem = document.getElementById('data-price');
          myElem.innerHTML = '';
        } else {
          myElem = document.getElementById('data-status');
          myElem.innerHTML = 'СВОБОДЕН';
          if(myElem.classList.contains('red-font')){
            myElem.classList.remove('red-font');
            myElem.classList.add('green-font');
          }
          myElem.classList.add('green-font');

          myElem = document.getElementById('data-area');
          myElem.innerHTML = data1 + ' м&#178';
          myElem = document.getElementById('data-price');
          /*myElem.innerHTML = data2 + ' <span class="rubas-img"></span>';*/
          myElem.innerHTML = data2;
        }
      }
      function HideInfoWin(){
        var myElem = document.getElementById('dad-info-panel');
        myElem.style.display='none';
      }
            const area_cost = 1400;
      //Процентная ставка
      const interests = {
          NaN : NaN,
          1 : 0.1,
          2 : 0.11,
          3 : 0.12,
          5 : 0.15
      };

      //Расчет ежемесячных выплат (ПЛТ в Excel)
      function monthly(ir, np, pv, fv, type) {
          var pmt, pvif;

          fv || (fv = 0);
          type || (type = 0);

          if (ir === 0)
              return -(pv + fv)/np;

          pvif = Math.pow(1 + ir, np);
          pmt = - ir * pv * (pvif + fv) / (pvif - 1);

          if (type === 1)
              pmt /= (1 + ir);

          return pmt;
      }

      //Вставка пробелов каждые 3 разряда для чисел
      function AddRadixSpaces(str) {
          var res = ''
          for (var i = 0; i < str.length; i++) {
              res += str[i]
              if ((str.length - i - 1) %% 3 === 0) {
                  if (i !== str.length - 1) {
                      res += (' ')
                  }
              }
          }
          return res
      }

      //Стоимость площади без учета процентов
      function GetCost() {
          return parseInt($('#price-input').val().split(' ').join(''));
      }

      //Заполнение надписей в форме значениями
      function InitValues() {
          //Заполнение цены за 100 кв.м.
          var cost_elem = $('#price');
          cost_elem.val((area_cost * 100).toString() + '\u20BD');

          //Заполнение процентных ставок для разных сроков рассрочки
          var div_years = $('#years-fields');
          div_years.find('input').each(function () {
              $(this).val((interests[parseInt($(this).attr('name'))] * 100).toString() + '%%');
          });

          //Заполнение селектора номера участка
          FillSelect();
      }

      //Считывание данных с формы
      function ProcessInput() {
          var yearn = parseInt($('#years-select').val());
          var input_values = {
              area : parseInt($('#area-input').val()),
              initial : parseInt($('#invest-input').val()),
              years : yearn,
              price : GetCost(),
              interest : interests[yearn]
          }
          return input_values;
      }

      //Расчет оплаты
      function Calculate(params) {
          var result = {
               //Оплата без рассрочки
              monthly : '',
              remainder : params.price,
              total : params.price,
              overpay : ''
          };
          if (!isNaN(params.years)) {
              //Оплата с рассрочкой
              var credit_cost = params.price - params.initial;
              result.monthly = -Math.round(monthly(params.interest / 12, params.years * 12, credit_cost));
              result.remainder = result.monthly * params.years * 12;
              result.total = result.remainder + params.initial;
              result.overpay = result.total / params.price - 1.0;
          }
          return result;
      }

      //Вывод значений в форму
      function UpdateValues(result) {
          if ($('#plot-select').val()) {
              $('input[name="price-area-perc-calc"]').val(result.total.toString() ? AddRadixSpaces(result.total.toString()) + '\u20BD' : '').css({'background-color' : 'lightblue', 'color' : 'white'});
              $('input[name="invest-calc"]').val(result.monthly.toString() ? AddRadixSpaces(result.monthly.toString()) + '\u20BD' : '').css({'background-color' : 'lightblue', 'color' : 'white'});
              $('input[name="residue-calc"]').val(AddRadixSpaces(result.remainder.toString()) + '\u20BD').css({'background-color' : 'lightblue', 'color' : 'white'});
              $('input[name="markup-calc"]').val((Math.round(result.overpay * 1000) / 10).toString() + '%%').css({'background-color' : 'lightblue', 'color' : 'white'});
          }
      }

      $.validator.addMethod('less', function(value, element) {
          return this.optional(element) || value >= Math.round(GetCost() / 10) || 0;
      });

      $.validator.addMethod('more', function(value, element) {
          return this.optional(element) || value < GetCost();
      });

      //Валидатор ввода
      function ValidateInput() {
          $('#credit-calc-form').validate({
              rules: {
                  'area-input' : {
                      required : true,
                      digits : true
                  },
                  'invest-input' : {
                      required : true,
                      digits : true,
                      less : Math.round(GetCost() / 10) || 0,
                      more : GetCost()
                  }
              },
              messages: {
                  'area-input' : {
                      required : "Введите площадь",
                      digits : "Введите целое число"
                  },
                  'invest-input' : {
                      required : "Введите первоначальный взнос",
                      digits : "Введите целое число",
                      less : "Минимальный первоначальный взнос 10%%",
                      more : "Первоначальный взнос не может превышать стоимость"
                  }
              },
              submitHandler : function(form) {
                  UpdateValues(Calculate(ProcessInput()));
              }
          });
      }

      //Обновление минимального начального взноса
      function UpdateMinInit() {
          var min_init = Math.round(GetCost() / 10) || 0;
          if (parseInt($('#years-select').val())) {
      //        $('#invest-input').attr('placeholder', 'Минимум ' + min_init + '\u20BD');
              $('#invest-input').val(min_init);
              $('#invest-input').removeAttr('disabled');
          } else {
      //        $('#invest-input').attr('placeholder', '');
              $('#invest-input').val('');
              $('#invest-input').attr('disabled', '');
          }
      }

      //////////////////////
      //Работа с участками//
      //////////////////////

      function GetPlotInfo() {
          var array = []
        for(var i = 1; i < total_plots; i++){
          record = myPlots['p' + i].split('|');
              array.push(record);
        }
          return array;
      }

      var plotInfo = GetPlotInfo();

      //Заполнение селектора номера участка
      function FillSelect() {
          plotInfo.forEach(function(plot, ind) {
              if(plot[0] !== '0') {
                  var area = plot[1];
                  var cost = plot[2];
                  $('#plot-select').append($("<option/>", {
                      html: `${ind + 1}. Площадь: ${area} м&#178;. Стоимость: ${cost} &#8381;`,
                      value: ind
                  }));
              }
          });
      }

      //Обновление полей стоимости и площади участка
      function UpdateAreaCost() {
          var plot_ind = parseInt($("#plot-select").val());
          if (isNaN(plot_ind)) {
              $("#area-input").val('');
              $("#price-input").val('');
          } else {
              $("#area-input").val(plotInfo[plot_ind][1]);
              $("#price-input").val(plotInfo[plot_ind][2]);
          }
      }

      //Обновление входных полей
      function UpdateFields(event) {
          //Обновление полей стоимости и площади участка
          UpdateAreaCost();
          //Обновление минимального начального взноса
          if (event.target.id !== 'invest-input') {
              UpdateMinInit();
          }
      }

      //Handler клика по участку
      var prev_select = $('#plot-select').children().first();
      function PlotClickHander(event) {
        //   var plot_ind = parseInt(event.target.id.slice(1)) - 1;
          var plot_ind = parseInt(Number(event.target.id) - 1);
          opt = $('#plot-select').children('option[value=' + plot_ind + ']');
          opt.attr('selected', 'selected');
          prev_select.removeAttr('selected');
          prev_select = opt;
          $('#credit-calc-form').trigger('change');
      }

      //Привязка handler'ов к элементам
      function BindHandlers() {
          //При измнении формы обновляются поля
          $('#credit-calc-form').on('change', UpdateFields);
          //При нажатии на кнопку "Расчет" запускается валидация
          $('#costing-btn').on('click', ValidateInput);
          //При нажатии на участок он выбирается для расчета
          for (var i = 0; i < total_plots; i++) {
            //   $('#p' + (i + 1)).on('click', PlotClickHander);
              $('#' + String(i + 1)).on('click', PlotClickHander);
          }
      }

      $(document).ready(function () {
          InitValues();
          UpdateMinInit();
          BindHandlers();
      });
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
