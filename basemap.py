import webbrowser
from math import cos, sin, radians

import folium


def dms_to_dd(deg, min, sec, dir):
    dd = deg + (min / 60) + (sec / 3600)
    if dir in ['W', 'S']:
        dd = -dd
    return dd


NICE_LOC_DD = (dms_to_dd(43, 44, 12, "N"), dms_to_dd(7, 15, 27, "E"))
OM_DATAS = {
    "F4JTV": [[dms_to_dd(43, 50, 2, "N"), dms_to_dd(7, 28, 18, "E")], 280],
    "F4IVI": [[dms_to_dd(43, 38, 35, "N"), dms_to_dd(7, 00, 44, "E")], 30],
    "F4IJR": [[dms_to_dd(43, 41, 23, "N"), dms_to_dd(7, 18, 3, "E")], 320]
            }

m = folium.Map(location=NICE_LOC_DD, zoom_start=10)
m.add_child(folium.LatLngPopup())

"""for key, value in OM_DATAS.items():

    origin_point = value[0]
    tooltip = key
    angle = value[1]

    folium.Marker(location=origin_point,
                  popup=f"Latitude:{round(value[0][0], 4)}\nLongitude:{round(value[0][1], 4)}",
                  radius=5,
                  tooltip=tooltip,
                  icon=folium.Icon(color='red', icon='male', prefix="fa")).add_to(m)

    end_lat = origin_point[0] + cos(radians(angle))
    end_lon = origin_point[1] + sin(radians(angle))

    folium.PolyLine([origin_point, [end_lat, end_lon]]).add_to(m)"""

m.save("./basemap.html")
webbrowser.open("./basemap.html")
