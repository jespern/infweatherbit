import time
import toml
import requests

from datetime import datetime

from influxdb import InfluxDBClient

CONST_BASE_URL = 'http://api.weatherbit.io/v2.0/current'
CONST_CFG_FN = 'config.toml'

if __name__ == '__main__':
    delay = 60
    config = {}

    with open(CONST_CFG_FN) as fp:
        config = toml.load(fp)
        delay = int(config['delay'])

    client = InfluxDBClient('172.16.1.56', 8086, 'username', 'password', 'telegraf')
    client.create_database('weatherbit')

    while True:
        now = datetime.utcnow()

        req = requests.get(CONST_BASE_URL, {
            'key': config['api_key'],
            'lat': config['lat'],
            'lon': config['lon']
        })

        resp = req.json()
        count = resp['count']

        if count >= 1:
            data = resp['data'][0]
            tags = {}

            for tag in ['country_code', 'city_name', 'station']:
                tags[tag] = data.pop(tag)

            for ignore in ['last_ob_time', 'ob_time', 'timezone', 
                           'datetime', 'pod']:
                if ignore in data:
                    data.pop(ignore)

            # Rewrite description
            weather = data.pop('weather')
            data['description'] = weather['description']

            # Ensure floats
            for fl in ['rh', 'lon', 'pres', 'clouds', 'solar_rad',
                       'wind_spd', 'slp', 'vis', 'h_angle', 'dni',
                       'dewpt', 'snow', 'uv', 'precip', 'wind_dir',
                       'ghi', 'dhi', 'aqi', 'lat', 'temp',
                       'elev_angle', 'app_temp']:
                data[fl] = float(data[fl])

            json_body = [
                {
                    "measurement": "weather",
                    "tags": tags,
                    "time": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "fields": data,
                }
            ]

            print(json_body)

            client.write_points(json_body)

        time.sleep(delay)