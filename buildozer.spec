[app]
# (str) Назва вашого додатку
title = PC Remote

# (str) Назва пакету (тільки латиниця, без пробілів)
package.name = pcremote

# (str) Домен пакету
package.domain = org.pcremote

# (str) Каталог з вихідним кодом
source.dir = .

# (list) Розширення файлів, що включаються в збірку
source.include_exts = py,png,jpg,kv,atlas

# (str) Версія додатку
version = 1.0.0

# (list) Залежності додатку
requirements = python3,kivy

# (str) Орієнтація екрану (portrait / landscape / all)
orientation = portrait

# ================= НАЛАШТУВАННЯ ДЛЯ ANDROID 9 ТА ANDROID 13 =================
# Автоматична згода з ліцензіями Android SDK (ОБОВ'ЯЗКОВО для GitHub Actions!)
android.accept_sdk_license = True

# android.minapi = 28 забезпечує підтримку Android 9 (Pie)
android.minapi = 28

# android.api = 33 націлює збірку на Android 13 (Tiramisu)
android.api = 33

# NDK API рівень
android.ndk_api = 28

# (list) Архітектури процесорів:
# arm64-v8a (64-біт для Android 13 та сучасних телефонів)
# armeabi-v7a (32-біт для старших пристроїв та Android 9 32-bit)
android.archs = arm64-v8a, armeabi-v7a

# Дозволи Android (Мережа та Вібрація)
android.permissions = INTERNET, ACCESS_NETWORK_STATE, VIBRATE

# Дозвіл на незашифровані HTTP з'єднання в локальній мережі (cleartext)
android.manifest.cleartext_traffic = True

# Автоматичний бекап
android.allow_backup = True

# Повноекранний режим
fullscreen = 0

[buildozer]
# Рівень логування (2 = повний лог помилок)
log_level = 2

# Шлях збереження готового APK
bin_dir = ./bin
