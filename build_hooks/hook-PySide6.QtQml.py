"""Keep the QML modules Lisa imports; avoid shipping an unused browser engine."""
from PyInstaller.utils.hooks.qt import add_qt6_dependencies,pyside6_library_info

hiddenimports,binaries,datas=add_qt6_dependencies(__file__)
qml_binaries,qml_datas=pyside6_library_info.collect_qtqml_files()


def needed(entry):
    path=str(entry[0]).replace("\\","/")
    if "/qml/" not in path:return True
    module=path.split("/qml/",1)[1].split("/",1)[0]
    return module in {"QtQuick","QtQml","QtMultimedia","QtCore"}


binaries += [entry for entry in qml_binaries if needed(entry)]
datas += [entry for entry in qml_datas if needed(entry)]
