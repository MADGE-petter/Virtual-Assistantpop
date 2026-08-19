"""
Interactive Alert Handler - Xử lý alert tương tác với người dùng.
"""

import re
import threading
import time
from typing import Callable, Dict, List, Optional, Union

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

from service.system_monitoring_service import (
    get_top_cpu_processes,
    get_top_ram_processes,
)

from .types import Alert


class InteractiveAlertHandler:
    """Xử lý trạng thái và phản hồi cho interactive alerts."""

    def __init__(self, interactive_callback: Optional[Callable] = None):
        self.interactive_callback = interactive_callback
        self._interactive_alerts: Dict[str, dict] = {}

    def is_interactive_alert(self, alert: Alert) -> bool:
        return alert.metric in ["ram", "temperature"] and alert.value >= 80.0

    def handle_alert(self, alert: Alert):
        metric = alert.metric

        with threading.RLock():
            if metric not in self._interactive_alerts:
                self._interactive_alerts[metric] = {
                    'alert': alert,
                    'state': 'waiting_confirmation',
                    'last_prompt': time.time(),
                    'reminder_count': 0
                }
                if self.interactive_callback:
                    self.interactive_callback(alert, 'ask_details')
            else:
                state = self._interactive_alerts[metric]
                if time.time() - state['last_prompt'] > 600:
                    state['last_prompt'] = time.time()
                    state['reminder_count'] += 1
                    if self.interactive_callback:
                        self.interactive_callback(alert, 'remind')

    def check_reminders(self):
        current_time = time.time()

        with threading.RLock():
            for metric, state in list(self._interactive_alerts.items()):
                if current_time - state['last_prompt'] > 600:
                    state['last_prompt'] = current_time
                    state['reminder_count'] += 1
                    if self.interactive_callback:
                        self.interactive_callback(state['alert'], 'remind')

    def clear_alert(self, metric: str):
        with threading.RLock():
            self._interactive_alerts.pop(metric, None)

    def handle_response(self, metric: str, response: str, context: dict = None):
        with threading.RLock():
            if metric not in self._interactive_alerts:
                return

            state = self._interactive_alerts[metric]
            alert = state['alert']

            if state['state'] == 'waiting_confirmation':
                if self._is_positive_response(response):
                    state['state'] = 'showing_details'
                    state['last_prompt'] = time.time()
                    if self.interactive_callback:
                        self.interactive_callback(alert, 'show_details')
                else:
                    state['last_prompt'] = time.time()

            elif state['state'] == 'showing_details':
                if self._is_positive_response(response):
                    state['state'] = 'waiting_close_selection'
                    state['last_prompt'] = time.time()
                    if self.interactive_callback:
                        self.interactive_callback(alert, 'ask_close_app')
                else:
                    state['last_prompt'] = time.time()

            elif state['state'] == 'waiting_close_selection':
                apps_to_close = self._parse_app_selection(response, context or {})
                if apps_to_close:
                    if isinstance(apps_to_close, list):
                        results = []
                        for app in apps_to_close:
                            success = self._close_process(app)
                            results.append((app, success))
                        succeeded = [app for app, ok in results if ok]
                        failed = [app for app, ok in results if not ok]
                        if succeeded:
                            del self._interactive_alerts[metric]
                            if self.interactive_callback:
                                self.interactive_callback(alert, 'close_success', {'closed_apps': succeeded, 'failed_apps': failed})
                        elif self.interactive_callback:
                            self.interactive_callback(alert, 'close_failed', {'failed_apps': failed})
                    else:
                        success = self._close_process(apps_to_close)
                        if success:
                            del self._interactive_alerts[metric]
                            if self.interactive_callback:
                                self.interactive_callback(alert, 'close_success', {'closed_app': apps_to_close})
                        else:
                            if self.interactive_callback:
                                self.interactive_callback(alert, 'close_failed', {'failed_app': apps_to_close})
                else:
                    if self.interactive_callback:
                        self.interactive_callback(alert, 'ask_close_app')

    def get_context(self, metric: str) -> dict:
        if metric not in self._interactive_alerts:
            return {}

        if self._interactive_alerts[metric]['state'] not in ['showing_details', 'waiting_close_selection']:
            return {}

        if metric == 'ram':
            processes = get_top_ram_processes(5)
        else:
            processes = get_top_cpu_processes(5)

        return {'top_processes': processes}

    def _is_positive_response(self, response: str) -> bool:
        positive_words = ['có', 'yes', 'ok', 'được', 'ừ', 'vâng', 'tôi muốn', 'show', 'xem', 'đóng']
        negative_words = ['không', 'no', 'khỏi', 'thôi', 'bỏ qua', 'skip']
        response_lower = response.lower()
        for word in negative_words:
            if word in response_lower:
                return False
        for word in positive_words:
            if word in response_lower:
                return True
        return False

    def _parse_app_selection(self, response: str, context: dict) -> Optional[Union[dict, List[dict]]]:
        response_lower = response.lower()

        if 'top_processes' in context:
            top_processes = context['top_processes']
            selected = []

            matches = re.findall(r'\b(?:app|số)?\s*(\d+)\b', response_lower)
            for match in matches:
                app_index = int(match) - 1
                if 0 <= app_index < len(top_processes):
                    proc = top_processes[app_index]
                    if proc not in selected:
                        selected.append(proc)

            for proc in top_processes:
                if proc['name'].lower() in response_lower and proc not in selected:
                    selected.append(proc)

            if selected:
                return selected if len(selected) > 1 else selected[0]

        return None

    def _close_process(self, process_info: dict) -> bool:
        try:
            pid = process_info.get('pid')
            name = process_info.get('name')
            if pid:
                proc = psutil.Process(pid)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    proc.kill()
                return True
            elif name:
                closed_count = 0
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] and name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            closed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return closed_count > 0
        except Exception:
            return False
        return False
