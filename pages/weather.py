"""Weather — current conditions from wttr.in (free, no API key needed)."""
import json
import urllib.request
import time
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()

# wttr.in JSON format — returns current weather for auto-detected location
WEATHER_URL = "https://wttr.in/?format=j1"


class PageWeather(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._last_fetch = 0

    def _fetch_weather(self):
        self._tick += 1
        # Only fetch every 10 minutes (600 ticks at ~1/s)
        now = time.time()
        if self._cache and (now - self._last_fetch) < 600:
            return self._cache

        try:
            req = urllib.request.Request(
                WEATHER_URL,
                headers={'User-Agent': 'compass-oled/1.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                current = data['current_condition'][0]
                self._cache = {
                    'temp_f': current.get('temp_F', '?'),
                    'temp_c': current.get('temp_C', '?'),
                    'feels_f': current.get('FeelsLikeF', '?'),
                    'desc': current.get('weatherDesc', [{}])[0].get('value', '?'),
                    'humidity': current.get('humidity', '?'),
                    'wind_mph': current.get('windspeedMiles', '?'),
                    'wind_dir': current.get('winddir16Point', '?'),
                    'area': data.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', ''),
                }
                self._last_fetch = now
        except Exception as e:
            if not self._cache:
                self._cache = {'temp_f': '?', 'temp_c': '?', 'feels_f': '?',
                               'desc': 'offline', 'humidity': '?',
                               'wind_mph': '?', 'wind_dir': '', 'area': ''}
        return self._cache

    def main(self, oled, data, config):
        w = self._fetch_weather()
        oled.clear()

        # Header
        oled.draw_text('WEATHER', 0, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # Temperature (large)
        oled.draw_text(f"{w['temp_f']}F", 0, 14, size=18, font_path=font)
        oled.draw_text(f"feels {w['feels_f']}F", 70, 18, size=9, font_path=font)

        # Condition
        desc = w['desc'][:20]
        oled.draw_text(desc, 0, 35, size=11, font_path=font)

        # Wind + humidity
        oled.draw_text(f"Wind: {w['wind_mph']}mph {w['wind_dir']}", 0, 50, size=9, font_path=font)
        oled.draw_text(f"Hum: {w['humidity']}%", 90, 50, size=9, font_path=font)

        oled.display()
