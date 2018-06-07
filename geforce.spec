# -*- mode: python -*-

block_cipher = None


a = Analysis(['geforce.py'],
             binaries=[],
             datas=[("window.ui", ".")],
             hiddenimports=["pygubu.builder.tkstdwidgets",
"pygubu.builder.ttkstdwidgets",
"pygubu.builder.widgets.dialog",
"pygubu.builder.widgets.editabletreeview",
"pygubu.builder.widgets.scrollbarhelper",
"pygubu.builder.widgets.scrolledframe",
"pygubu.builder.widgets.tkscrollbarhelper",
"pygubu.builder.widgets.tkscrolledframe",
"pygubu.builder.widgets.pathchooserinput"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='geforce',
          debug=False,
          strip=False,
          upx=True,
          console=True )
