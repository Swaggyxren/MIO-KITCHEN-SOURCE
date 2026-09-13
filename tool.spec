# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['PySide6', 'PIL']
datas += collect_data_files('androguard')
hiddenimports += collect_submodules('src')
tmp_ret = collect_all('qfluentwidgets')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['tool.py'],
    pathex=['.', 'src', 'src/core', 'src/qt_layer'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy'],
    noarchive=False,
    optimize=0,
)

if sys.platform.startswith('linux'):
    # Exclude libxkbcommon so Qt dynamically links to the host's libxkbcommon matching host XKB files.
    # Bundling an older libxkbcommon (e.g. from Ubuntu 22.04) causes segmentation faults on modern
    # Linux distributions (Arch, Fedora, CachyOS) when parsing host XKB keymaps (e.g. on screenshot/key events).
    a.binaries = [x for x in a.binaries if not any(k in x[0] for k in ('libxkbcommon', 'libxkbcommon-x11'))]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
