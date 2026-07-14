import requests
import json
import time

SERVERS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

HEADERS = {
    "User-Agent": "WaterMapBot/1.0 (https://github.com/akkauntbravl549-afk/WaterMap)"
}

overpass_query = """
[out:json][timeout:90];
area["ISO3166-2"="RU-MOW"]->.searchArea;
(
  node["name"~"Drinkit|Дринкит",i](area.searchArea);
  way["name"~"Drinkit|Дринкит",i](area.searchArea);
  node["brand"~"Drinkit|Дринкит",i](area.searchArea);
  way["brand"~"Drinkit|Дринкит",i](area.searchArea);
);
out center body;
"""

data = None

for server in SERVERS:
    try:
        print(f"Запрос к серверу: {server}")
        response = requests.post(server, data={'data': overpass_query}, headers=HEADERS, timeout=90)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Успешно получены данные Дринкит!")
                break
            except json.JSONDecodeError:
                print(f"Сервер {server} прислал HTML вместо JSON. Пробуем следующий...")
        else:
            print(f"Сервер {server} ответил с кодом {response.status_code}")
    except Exception as e:
        print(f"Ошибка подключения к {server}: {e}")
    
    time.sleep(2)

if not data:
    raise RuntimeError("Ни один сервер Overpass не ответил корректно. Попробуйте запустить позже.")

points = []
for item in data.get('elements', []):
    if item.get('type') == 'node':
        lat = item.get('lat')
        lon = item.get('lon')
    elif item.get('type') == 'way' and 'center' in item:
        lat = item['center'].get('lat')
        lon = item['center'].get('lon')
    else:
        continue

    tags = item.get('tags', {})
    name = tags.get('name', 'Кофейня Дринкит')
    
    street = tags.get('addr:street', '')
    house = tags.get('addr:housenumber', '')
    
    address = f"ул. {street}, д. {house}".strip(", d. ") if street else "Адрес не указан (см. на карте)"
        
    points.append({
        "title": name,
        "address": address,
        "lat": lat,
        "lng": lon,
        "type": "coffee"
    })

print(f"Собрано кофеен Дринкит: {len(points)}")

with open('drinkit.json', 'w', encoding='utf-8') as f:
    json.dump(points, f, ensure_ascii=False, indent=2)

print("Файл drinkit.json успешно создан!")
