"""Owner-only activation provisioning. Secrets go through stdin, never logs/args."""
import argparse,base64,csv,hashlib,json,os,secrets,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from activation import _b64 as b64, KEY_ID, ISSUER, AUDIENCE, PURCHASE_URL
def private_root():
    configured=os.environ.get('LISA_OWNER_PRIVATE')
    if not configured:raise RuntimeError('Set LISA_OWNER_PRIVATE to a private folder outside the public source repository.')
    path=Path(configured).resolve()
    if path==ROOT or ROOT in path.parents:raise RuntimeError('Private folder must be outside source.')
    path.mkdir(parents=True,exist_ok=True);return path
def setup():
    from core import dpapi
    from cryptography.hazmat.primitives.asymmetric import ec
    path=private_root()/'license-signing.dpapi'
    if path.exists():key=json.loads(dpapi(path.read_bytes(),True))
    else:
        if (ROOT/'activation-public.json').exists():raise RuntimeError('Restore the original signing backup; refusing to replace an existing verification key.')
        native=ec.generate_private_key(ec.SECP256R1()).private_numbers()
        key={'kty':'EC','crv':'P-256','x':b64(native.public_numbers.x.to_bytes(32,'big')),'y':b64(native.public_numbers.y.to_bytes(32,'big')),'d':b64(native.private_value.to_bytes(32,'big')),'kid':KEY_ID}
        path.write_bytes(dpapi(json.dumps(key).encode()))
    public={k:v for k,v in key.items() if k!='d'};public.update(alg='ES256',use='sig')
    cfg={'base_url':'https://lisa-control-center.kitty-ai.workers.dev','issuer':ISSUER,'audience':AUDIENCE,'purchase_url':PURCHASE_URL,'keys':[public]}
    (ROOT/'activation-public.json').write_text(json.dumps(cfg,indent=2))
    print('Packaged public verification key ready. Private signing key preserved outside source.')
def codes(count,batch):
    directory=private_root();file=directory/(batch+'-activation-codes.csv')
    if file.exists():raise RuntimeError('Batch already exists. Preserve original codes; do not regenerate.')
    now=int(time.time());rows=[];sql=[]
    for i in range(count):
        token=base64.b32encode(secrets.token_bytes(19)).decode().rstrip('=')[:30]
        code='LISA-'+'-'.join(token[n:n+5] for n in range(0,30,5));id=batch+'-'+str(i+1).zfill(3)
        digest=hashlib.sha256(code.encode()).hexdigest()
        rows.append({'license_id':id,'activation_code':code,'status':'unclaimed'})
        sql.append("INSERT INTO activation_codes(id,code_hash,created_at) VALUES('"+id+"','"+digest+"',"+str(now)+");")
    with file.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['license_id','activation_code','status']);writer.writeheader();writer.writerows(rows)
    (directory/(batch+'-digests.sql')).write_text('\n'.join(sql))
    print(str(count)+' codes generated in the private owner folder. No code is printed.')
def deploy_key():
    from core import dpapi
    key=dpapi((private_root()/'license-signing.dpapi').read_bytes(),True)
    node=ROOT/'control-center/node_modules/node/bin/node.exe';cli=ROOT/'control-center/node_modules/wrangler/bin/wrangler.js'
    p=subprocess.run([str(node),str(cli),'secret','put','LICENSE_SIGNING_KEY'],cwd=ROOT/'control-center',input=key,capture_output=True)
    if p.returncode:raise RuntimeError('Signing key deployment failed. Check owner Cloudflare login; no secret output is shown.')
    print('Activation signing key installed. Existing VAULT_KEY was not changed.')
def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['setup','codes','deploy-key']);p.add_argument('--count',type=int,default=50);p.add_argument('--batch',default='lisa22-sale');a=p.parse_args()
    if a.operation=='setup':setup()
    elif a.operation=='deploy-key':deploy_key()
    else:
        if not 1<=a.count<=1000 or not all(c.isalnum() or c=='-' for c in a.batch):raise ValueError('Invalid batch')
        codes(a.count,a.batch)
if __name__=='__main__':main()
