# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# DLLs the game doesn't need, left out to make the download smaller: OpenGL
# (the game draws everything without it), encryption, and Qt modules for QML
# and D-Bus. Compared by file name, ignoring case. Not left out, although they
# look unused (checked against what each kept DLL imports):
# - MSVCP140.dll: the Visual C++ runtime, which not every PC has
# - Qt5Network.dll: Qt5Multimedia.dll (the sounds) needs it, and without it the game won't start
# - Qt5Svg.dll, Qt5Test.dll: pyqtgraph imports PyQt5.QtSvg and PyQt5.QtTest, which need them
excluded_binaries = [
    'opengl32sw.dll',
    'd3dcompiler_47.dll',
    'libglesv2.dll',
    'libegl.dll',
    'mfc140u.dll',
    'libcrypto-1_1-x64.dll',
    'libssl-1_1-x64.dll',
    'qt5quick.dll',
    'qt5qml.dll',
    'qt5qmlmodels.dll',
    'qt5websockets.dll',
    'qt5dbus.dll',
    # Qt plugins that are never used on Windows (showing the game in a web
    # browser, and a Linux desktop feature), and that need DLLs left out above
    'qwebgl.dll',
    'qxdgdesktopportal.dll',
]

# Python packages the game never uses, which are only bundled because other
# packages (pyqtgraph) can optionally use them: matplotlib (and the packages it
# needs), Pillow, and a few more. Checked by running the game and opening every
# window: none of these are loaded
excluded_modules = [
    'matplotlib',
    'PIL',
    'contourpy',
    'kiwisolver',
    'dateutil',
    'yaml',
    'charset_normalizer',
    'markupsafe',
    'tkinter',
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
             datas=[('deep_space_trader\\images', 'images'), ('deep_space_trader\\audio', 'audio'),
                    ('deep_space_trader\\translations', 'translations')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=excluded_modules,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

def binfile_should_be_excluded(binfile):
    # Binaries are named by their path inside the bundle (e.g.
    # 'PyQt5\\Qt5\\bin\\opengl32sw.dll'), so only the file name is compared.
    # (Split on either slash, so this works whichever system builds it)
    name = binfile.replace('\\', '/').split('/')[-1].lower()
    if name in excluded_binaries:
        return True

    for prefix in excluded_libnames:
        if name.startswith(prefix.lower()) and name.endswith('.dll'):
            return True

    return False

excluded = [x[0] for x in a.binaries if binfile_should_be_excluded(x[0])]
print("Leaving out %d DLLs: %s" % (len(excluded), ", ".join(sorted(e.replace('\\', '/').split('/')[-1] for e in excluded))))
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
