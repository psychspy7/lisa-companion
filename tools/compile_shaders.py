"""Compile the editable Qt shaders for the shipped D3D/OpenGL/Metal render paths."""
from pathlib import Path
import os
import subprocess
import PySide6

root=Path(__file__).resolve().parents[1]
compiler=Path(PySide6.__file__).parent/('qsb.exe' if os.name=='nt' else 'qsb')
for source in sorted((root/'ui/shaders').glob('*.frag')):
    subprocess.run([str(compiler),'--glsl','100 es,120,150','--hlsl','50','--msl','12','-o',str(source.with_suffix('.frag.qsb')),str(source)],
                   check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
print('Lisa shader packages compiled.')
