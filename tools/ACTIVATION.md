# Lisa activation administration

Customers enter a personal code in the Windows activation screen. They need internet once, then the signed entitlement is checked locally at every launch. Google sign-in is only for the private owner website; it is not a customer requirement.

The 50 sale codes are in the owner's separate private CSV. Send one code to each buyer privately and record which license ID you sold. Do not put that CSV in GitHub, the public ZIP, a screenshot or an AI prompt. The database stores only code digests. A successful first redemption binds the license to the app's protected device identity and machine digest; retry/recovery with that identity is idempotent. Another device cannot redeem the same code.

The signing key is stored in the Cloudflare Worker secret LICENSE_SIGNING_KEY. A DPAPI-encrypted backup is retained outside source on the owner's original Windows account. It is not included in the public handover. Keep an additional private owner backup using your password manager or secure backup process. Never rotate the existing VAULT_KEY: that protects old provider credentials.

If an activated customer reinstalls Lisa on the same Windows account and PC, keep LocalAppData/LISA/activation-device.key and activation-receipt.jwt. Updates and uninstall preserve the private data folder. Recover activation uses the original protected device key. A reset/lost key or a replaced PC requires owner help and a replacement code; do not promise unlimited device transfer.

To provision a new batch from source, install Python 3.12 requirements, set LISA_OWNER_PRIVATE to a private folder outside the repository and run:
```powershell
python tools/manage_activation.py codes --count 50 --batch lisa-next-sale
```
Import the generated digest SQL into this Lisa D1 database using the authenticated Cloudflare CLI. Never import plaintext codes. Run setup only with the original signing backup present; it creates packaged public verification configuration. deploy-key sends the decrypted secret through stdin, without logging it. The owner controls account CLI credentials separately.

Public protocol: /api/license/config, /challenge, /redeem, /recover. Private license list/disable is /api/admin/licenses after verified owner Google authentication. The protected console can list claimed IDs; sale-code assignment remains in the owner's private ledger.

Security limits: source-visible desktop DRM can be patched by a determined attacker. Signed receipts prevent straightforward forgery/copying in the normal app. Lifetime offline access means a previously issued receipt cannot be revoked while that device stays offline. Disabling a code blocks later online activation/recovery, not existing offline use.
