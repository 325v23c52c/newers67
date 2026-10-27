[app]
title = PC Remote
package.name = pcremote
package.domain = org.pcremote
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy
orientation = portrait

android.accept_sdk_license = True
android.minapi = 28
android.api = 33
android.ndk_api = 28
android.archs = arm64-v8a, armeabi-v7a
android.permissions = INTERNET, ACCESS_NETWORK_STATE, VIBRATE
android.manifest.cleartext_traffic = True
android.allow_backup = True
fullscreen = 0

[buildozer]
log_level = 2
bin_dir = ./bin
