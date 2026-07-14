import requests
import json

overpass_url = "https://overpass-api.de/api/interpreter"
overpass_query = """
[out:json];
area["ISO3166-2"="RU-MOW"]->.searchArea;
(
  node["amenity"="clinic"](area.searchArea);
  node["amenity"="hospital"](area.searchArea);
);
out body;
"""

print("Скачиваем данные из OpenStreetMap...")
response = requests.post(overpass_url, data={'data': overpass_query})
data = response.json()

points = []

for item in data.get('elements', []):
    lat = item.get('lat')
    lon = item.get('lon')
    tags = item.get('tags', {})
    
    name = tags.get('name', 'Городская поликлиника')
    address = tags.get('addr:street', '')
    if tags.get('addr:housenumber'):
        address += f", д. {tags.get('addr:housenumber')}"
        
    points.append({
        "title": name,
        "address": address,
        "lat": lat,
        "lng": lon,
        "type": "polyclinic"
    })

print(f"Собрано точек: {len(points)}")

with open('polyclinics.json', 'w', encoding='utf-8') as f:
    json.dump(points, f, ensure_ascii=False, indent=2)

print("Файл polyclinics.json успешно создан!")
