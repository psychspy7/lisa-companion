# Lisa private control center

Separate Cloudflare Worker + D1 namespace, Firebase Google identity. This lives in Lisa's own repository and does not access Kitty AI or the company website's data.

Keys are written over authenticated HTTPS and encrypted at rest using AES-GCM; they are never returned to the browser or bundled in Lisa. The first cryptographically verified Google login of the configured owner pins its Firebase UID atomically in D1; subsequent admin checks require that pinned UID and the verified Google email. All provider calls are owner-only until a separate customer-access policy is implemented.

Setup/deploy: install dependencies with npm ci, run npm test and npm run build; configure the dedicated D1 database, public Firebase web configuration and a private VAULT_KEY secret, then apply the included migration and deploy. Enable Google sign-in for this Firebase project and add this console's domain to authorized domains. Do not enable billing or copy credentials from other projects.

The desktop pairing page requires a code shown by Lisa and expires after five minutes. Refresh credentials are encrypted during one-time handoff and stored with Windows DPAPI on the desktop. Source archives exclude local secret files.
