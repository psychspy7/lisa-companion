# Lisa private backend handover

Owner console: https://lisa-control-center.kitty-ai.workers.dev
Firebase project: lisa-kittycorp-20261011
Cloudflare Worker: lisa-control-center
D1 database: lisa-control-center

Google sign-in is enabled, the console domain is authorized, and the intended owner login has been verified and pinned. Provider credentials must be entered through the private console or migrated from the desktop after Google linking. Never paste credentials in a conversation.

The app menu opens Google linking. It displays a six-digit code. Approve the corresponding device in the signed-in console, return to Lisa and test a short reply. Use each provider card to load available models and test access. Save an ElevenLabs Voice ID or Fish reference ID before enabling cloud voice. Gemini or Groq can transcribe microphone turns. Vidu generation requires an explicit confirmation and account credits.

Keep the Cloudflare vault secret intact across deployments. Losing or replacing it makes existing provider ciphertext unreadable. Re-enter provider keys through the console if recovery is necessary. The D1 data and deployment secrets are separate from source ZIPs.

To redeploy, authenticate the official Firebase and Cloudflare tools in your own account, use control-center’s documented commands, and target only the Lisa resources above. No Firebase billing upgrade or paid generation was enabled during this build.
