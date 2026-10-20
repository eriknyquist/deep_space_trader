# -*- mode: python ; coding: utf-8 -*-

import os
import re

from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
)

block_cipher = None


def readPackageInfo():
    """
    The game's version and author (from deep_space_trader/__init__.py), and
    the copyright line (the first line of LICENSE)
    """
    with open(os.path.join(SPECPATH, 'deep_space_trader', '__init__.py'), encoding='utf-8') as fh:
        text = fh.read()
    version = re.search(r'__version__\s*=\s*"([^"]+)"', text).group(1)
    author = re.search(r'__author__\s*=\s*"([^"]+)"', text).group(1)

    with open(os.path.join(SPECPATH, 'LICENSE'), encoding='utf-8') as fh:
        copyright = fh.readline().strip()

    return version, author, copyright


def versionInfo():
    """
    Version information for the .exe file, shown in its Properties (Details tab):
    name, version, author and copyright, all taken from the project's files, so
    there's nothing extra to update for a new version
    """
    version, author, copyright = readPackageInfo()

    # Windows wants four numbers, e.g. (1, 5, 0, 0) for 1.5.0
    numbers = tuple(int(n) for n in version.split('.'))[:4]
    numbers += (0,) * (4 - len(numbers))

    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=numbers, prodvers=numbers, mask=0x3f, flags=0x0, OS=0x40004,
                          fileType=0x1, subtype=0x0, date=(0, 0)),
        kids=[
            StringFileInfo([
                StringTable('040904B0', [
                    StringStruct('CompanyName', author),
                    StringStruct('FileDescription', 'Deep Space Trader'),
                    StringStruct('FileVersion', version),
                    StringStruct('InternalName', 'Deep Space Trader'),
                    StringStruct('LegalCopyright', copyright + '. MIT license.'),
                    StringStruct('OriginalFilename', 'Deep Space Trader.exe'),
                    StringStruct('ProductName', 'Deep Space Trader'),
                    StringStruct('ProductVersion', version),
                ])
            ]),
            VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
        ])

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
          # Not compressed with UPX: it saves little, and UPX-packed programs
          # are often flagged by antivirus software
          upx=False,
          console=False,
          # The game's icon (in Explorer, the taskbar, and "Apps & features"),
          # and its name, version and copyright in the file's Properties
          icon=os.path.join(SPECPATH, 'deep_space_trader', 'images', 'icon.ico'),
          version=versionInfo())

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='Deep Space Trader')
