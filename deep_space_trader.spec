# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

excluded_binaries = [
    'opengl32sw.dll',
    'mfc140u.dll',
    'libcrypto-1_1.dll',
    'libGLESv2.dll',
    'libssl-1_1.dll',
    'MSVCP140.dll',
    'd3dcompiler_47.dll',
    'Qt5Quick.dll',
    'Qt5Qml.dll',
    'Qt5Network.dll',
    'Qt5Test.dll',
    'Qt5WebSockets.dll',
    'Qt5DBus.dll',
    'Qt5QmlModels.dll',
    'Qt5Svg.dll'
]

excluded_libnames = [
    'libopenblas',
    'libdgamln',
    'libbispeu',
    'lib_arpack',
    'libdfft',
    'hdf5',
    'libdfitpack',
    'sqlite3',
    'libspecfun',
    'libd_odr',
    'libvode-f2p',
    'libdqag',
    'liblbfgsb',
    'libbanded'
]

a = Analysis(['deep_space_trader\\__main__.py'],
             pathex=['deep_space_trader'],
             binaries=[],
             datas=[('deep_space_trader\\images', 'images'), ('deep_space_trader\\audio', 'audio')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

def binfile_should_be_excluded(binfile):
    if binfile in excluded_binaries:
        return True

    for name in excluded_libnames:
        if binfile.startswith(name) and binfile.endswith('.dll'):
            return True

    return False

a.binaries = [x for x in a.binaries if not binfile_should_be_excluded(x[0])]

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Deep Space Trader',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Deep Space Trader')
