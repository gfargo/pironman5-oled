"""GitHub Activity — recent events across repos."""
import json
import urllib.request
import time
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

GITHUB_USER = "gfargo"
EVENTS_URL = f"https://api.github.com/users/{GITHUB_USER}/events/public?per_page=10"


class PageGithubActivity(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._page = 0
        self._last_fetch = 0
        self._last_page_time = 0

    def _fetch_events(self):
        now = time.time()
        # Refresh every 15 minutes
        if self._cache and (now - self._last_fetch) < 900:
            return self._cache

        try:
            req = urllib.request.Request(
                EVENTS_URL,
                headers={'User-Agent': 'compass-oled/1.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                events = json.loads(resp.read())
                items = []
                for e in events[:8]:
                    repo = e.get('repo', {}).get('name', '?').split('/')[-1]
                    etype = e.get('type', '?').replace('Event', '')
                    # More readable event names
                    labels = {
                        'Push': 'push',
                        'PullRequest': 'PR',
                        'Create': 'new',
                        'Delete': 'del',
                        'Watch': 'star',
                        'Fork': 'fork',
                        'Issues': 'issue',
                        'IssueComment': 'cmnt',
                        'Release': 'rel',
                    }
                    label = labels.get(etype, etype[:5])
                    items.append(f"{label:<5} {repo[:15]}")
                self._cache = items
                self._last_fetch = now
        except Exception:
            if not self._cache:
                self._cache = ['offline']
        return self._cache

    def main(self, oled, data, config):
        events = self._fetch_events()
        self._tick += 1

        oled.clear()

        # Header
        oled.draw_text('GITHUB', 0, 0, size=10, font_path=font)
        oled.draw_text(f"@{GITHUB_USER}", 55, 0, size=9, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # Paginate: 4 events per view
        per_page = 4
        pages = max(1, (len(events) + per_page - 1) // per_page)
        now = time.time()
        if now - self._last_page_time > 4 and pages > 1:
            self._page = (self._page + 1) % pages
            self._last_page_time = now

        start = self._page * per_page
        for i, event in enumerate(events[start:start + per_page]):
            y = 15 + (i * 12)
            oled.draw_text(event[:22], 0, y, size=10, font_path=font)

        oled.display()
