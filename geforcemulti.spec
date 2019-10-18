# -*- mode: python -*-

block_cipher = None


a = Analysis(['geforcemulti.py'],
             pathex=['Z:\\windows_vms\\wavetrend.git\\src'],
             binaries=[],
             datas=[
                ('config.txt', '.'),
                ('style.qss', '.'),
                ('mainwindowqt.ui', '.'),
                ('trade.ui', '.'),
                ('windowqt.ui', '.'),
                ('aiprogress.ui', '.'),
                ('LICENSE', '.'),
                ('qss_icons\*', 'qss_icons'),
                ('logotop.ico', '.'),
                ('logotop.png', '.'),
                ('coin.ico', '.'),
                ('splashscreen.bmp', '.'),
                ('C:\Python37-amd64\Lib\_strptime.py', '.'),
                ],
             hiddenimports=['win32gui', 'win32api', 'win32con', 'sklearn.utils._cython_blas', 'sklearn.neighbors.typedefs', 'sklearn.neighbors.quad_tree', 'sklearn.tree._utils'],
             runtime_hooks=['winbuildhook.py'],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', "IPython"],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='wavetrend',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          console=True,
          icon='logotop.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               name='wavetrend')
