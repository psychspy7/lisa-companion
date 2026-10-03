LISA 1.1 repairs API configuration and adds hands-free conversation.

- Retired default Groq models migrate to a supported default. Gemini JSON MIME and model-specific settings are corrected; provider requests identify Lisa with an application user agent.
- Automatic chat backups: preferred service, then configured Groq, Gemini, OpenRouter and Meta Llama. Only configured services are called; the app names the successful provider. OpenRouter defaults to its free router. Meta uses the official direct Llama API and requires its own developer key and available model.
- Load available models and Test connection independently in Settings. API errors distinguish authentication, permissions, retired models, quota/rate limits and connection issues without revealing credentials. Encrypted key saves are atomic.
- Start talk: speak, pause, hear Lisa, speak again. Local end-of-turn detection ignores silence and retains pre-roll. Groq, Gemini, ElevenLabs and Fish transcription backups; cloud voice backup plus optional free Windows voice fallback. Mic pauses during replies; Interrupt cuts speech off. End talk, Stop, Esc, Settings and quit close the microphone. Sessions never start automatically.
- Per-user Windows installation, optional desktop shortcut, fullscreen UI and verified update support remain intact. Existing keys, custom prompts, memories and history settings are preserved.

Use Update in Lisa, or close Lisa and run LISA-Setup.exe. Add complete keys in Settings, choose models and voice IDs, then test each service. No keys are embedded. Automated provider and conversation tests use simulated services; authenticated live calls remain unverified because no relevant credentials are saved in the current Lisa data folder.
