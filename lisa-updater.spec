"""Small independent updater with no GUI framework or third-party imports."""
a=Analysis(['updater_worker.py'],pathex=[],binaries=[],datas=[],hiddenimports=[],
    excludes=['PySide6','numpy','PIL','sounddevice','tkinter'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='LISA-Updater',console=False,
    debug=False,strip=False,upx=False,icon=['assets/lisa.ico'])
