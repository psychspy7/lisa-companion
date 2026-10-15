"""Verify restored offline assets against the pinned, public manifest."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'offline'
def verify():
 manifest=json.loads((root/'manifest.json').read_text());expected={manifest['model']['file']:manifest['model']['sha256'],**{'runtime/'+k:v for k,v in manifest['runtime']['binaries'].items()}}
 for name,digest in expected.items():
  path=(root/name).resolve()
  if root.resolve() not in path.parents:raise ValueError('Invalid manifest path')
  with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  if actual!=digest:raise RuntimeError('Offline asset integrity mismatch: '+name)
 if (root/manifest['model']['file']).stat().st_size!=manifest['model']['bytes']:raise RuntimeError('Model size mismatch')
 print('Pinned offline model and '+str(len(expected)-1)+' runtime files verified.')
if __name__=='__main__':verify()
