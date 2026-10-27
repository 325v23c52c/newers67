# -*- coding: utf-8 -*-
"""
PC Remote Control - Android App (Kivy)
Сумісно з Android 9 (API 28), Android 13 (API 33), 32-bit (armeabi-v7a) та 64-bit (arm64-v8a)
3 Кнопки:
  1. Вимкнення ПК
  2. Режим сну
  3. Немає / Скасувати
"""

import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.utils import platform

# Спроба імпорту вібрації на Android
try:
    from plyer import vibrator
except Exception:
    vibrator = None

# Темний фон
Window.clearcolor = (0.06, 0.08, 0.12, 1)

class PCRemoteApp(App):
    def build(self):
        self.title = "PC Remote Control"
        
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Заголовок
        header = Label(
            text="[b]💻 Керування ПК[/b]",
            markup=True,
            font_size='22sp',
            size_hint=(1, 0.1),
            color=(0.9, 0.95, 1, 1)
        )
        main_layout.add_widget(header)

        # Панель налаштування IP комп'ютера
        ip_box = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
        
        self.ip_input = TextInput(
            text="192.168.1.100",
            multiline=False,
            font_size='16sp',
            background_color=(0.12, 0.16, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 10, 12, 10],
            hint_text="IP комп'ютера (наприклад 192.168.1.5)"
        )
        ip_box.add_widget(self.ip_input)

        btn_test = Button(
            text="Перевірка",
            size_hint=(0.35, 1),
            background_normal='',
            background_color=(0.15, 0.23, 0.36, 1),
            color=(0.3, 0.8, 1, 1),
            bold=True
        )
        btn_test.bind(on_release=self.check_status)
        ip_box.add_widget(btn_test)

        main_layout.add_widget(ip_box)

        # Статусний індикатор
        self.status_label = Label(
            text="Введіть локальний IP комп'ютера та натисніть кнопку",
            font_size='13sp',
            size_hint=(1, 0.08),
            color=(0.6, 0.7, 0.8, 1)
        )
        main_layout.add_widget(self.status_label)

        # ================= ОСНОВНІ 3 КНОПКИ =================
        buttons_layout = BoxLayout(orientation='vertical', spacing=14, size_hint=(1, 0.65))

        # 1. КНОПКА ВИМКНЕННЯ ПК (Червона)
        btn_shutdown = Button(
            text="[size=22sp][b]1. ⏻ ВИМКНЕННЯ ПК[/b][/size]\n[size=12sp]Надіслати команду вимкнення[/size]",
            markup=True,
            background_normal='',
            background_color=(0.85, 0.15, 0.15, 1),
            color=(1, 1, 1, 1)
        )
        btn_shutdown.bind(on_release=lambda x: self.confirm_action("shutdown", "Вимкнути комп'ютер?"))
        buttons_layout.add_widget(btn_shutdown)

        # 2. КНОПКА РЕЖИМ СНУ (Синьо-індиго)
        btn_sleep = Button(
            text="[size=22sp][b]2. ☾ РЕЖИМ СНУ[/b][/size]\n[size=12sp]Перевести комп'ютер у режим сну[/size]",
            markup=True,
            background_normal='',
            background_color=(0.28, 0.35, 0.85, 1),
            color=(1, 1, 1, 1)
        )
        btn_sleep.bind(on_release=lambda x: self.send_command("sleep"))
        buttons_layout.add_widget(btn_sleep)

        # 3. КНОПКА СКАСУВАТИ / НЕМАЄ (Сіро-бурштинова)
        btn_cancel = Button(
            text="[size=22sp][b]3. ✕ НЕМАЄ / СКАСУВАТИ[/b][/size]\n[size=12sp]Скасувати заплановане вимкнення ПК[/size]",
            markup=True,
            background_normal='',
            background_color=(0.3, 0.36, 0.44, 1),
            color=(0.95, 0.95, 0.95, 1)
        )
        btn_cancel.bind(on_release=lambda x: self.send_command("cancel"))
        buttons_layout.add_widget(btn_cancel)

        main_layout.add_widget(buttons_layout)
        return main_layout

    def trigger_vibrate(self):
        """Вібрація на Android при натисканні"""
        if platform == 'android' and vibrator:
            try:
                vibrator.vibrate(0.05)
            except Exception:
                pass

    def get_server_url(self, endpoint):
        ip = self.ip_input.text.strip()
        if not ip.startswith("http://") and not ip.startswith("https://"):
            ip = f"http://{ip}"
        if ":" not in ip.replace("http://", "").replace("https://", ""):
            ip = f"{ip}:5000"
        return f"{ip}{endpoint}"

    def check_status(self, instance):
        self.trigger_vibrate()
        self.status_label.text = "Підключення до ПК..."
        self.status_label.color = (0.9, 0.7, 0.2, 1)

        url = self.get_server_url("/status")
        UrlRequest(
            url,
            on_success=self.on_status_success,
            on_error=self.on_request_error,
            on_failure=self.on_request_error,
            timeout=3
        )

    def on_status_success(self, req, result):
        hostname = result.get('hostname', 'ПК')
        os_name = result.get('os', 'Windows')
        self.status_label.text = f"✔ Підключено: {hostname} ({os_name}) - Онлайн"
        self.status_label.color = (0.2, 0.85, 0.3, 1)

    def confirm_action(self, cmd, message):
        """Діалог підтвердження для критичної дії (Вимкнення)"""
        self.trigger_vibrate()
        box = BoxLayout(orientation='vertical', padding=15, spacing=15)
        box.add_widget(Label(text=message, font_size='16sp', halign='center'))

        btn_box = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.4))
        
        btn_yes = Button(text="Так, вимкнути", background_color=(0.85, 0.15, 0.15, 1), bold=True)
        btn_no = Button(text="Скасувати", background_color=(0.3, 0.35, 0.45, 1))

        btn_box.add_widget(btn_no)
        btn_box.add_widget(btn_yes)
        box.add_widget(btn_box)

        popup = Popup(
            title="Підтвердження",
            content=box,
            size_hint=(0.85, 0.4),
            auto_dismiss=True
        )

        btn_no.bind(on_release=popup.dismiss)
        def on_confirm(instance):
            popup.dismiss()
            self.send_command(cmd)

        btn_yes.bind(on_release=on_confirm)
        popup.open()

    def send_command(self, cmd):
        self.trigger_vibrate()
        self.status_label.text = f"Відправка команди: {cmd}..."
        self.status_label.color = (0.9, 0.7, 0.2, 1)

        url = self.get_server_url(f"/api?cmd={cmd}")
        UrlRequest(
            url,
            on_success=self.on_cmd_success,
            on_error=self.on_request_error,
            on_failure=self.on_request_error,
            timeout=5
        )

    def on_cmd_success(self, req, result):
        msg = result.get('message', 'Команду виконано!')
        self.status_label.text = f"✔ {msg}"
        self.status_label.color = (0.2, 0.85, 0.3, 1)

    def on_request_error(self, req, error):
        self.status_label.text = "✖ Помилка з'єднання! Перевірте IP та Wi-Fi"
        self.status_label.color = (0.95, 0.2, 0.2, 1)

if __name__ == '__main__':
    PCRemoteApp().run()
