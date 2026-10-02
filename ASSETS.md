# Artwork and motion provenance

The four main portraits were created using the built-in OpenAI image generation tool, using the user's selected Lisa references and a shared evening master as the identity reference. Originals are in `assets/portraits/*.png`. They are approximately 941 × 1672 pixels; original generator files are also retained in the user's Codex generated-images folder.

The 36 expressions come from the previously selected four 3 × 3 character atlases, retained as `assets/morning.png`, `afternoon.png`, `evening.png`, and `night.png`. Each group of nine has its own outfit. No external character art pack was used.

## Shared prompt brief

One clearly adult 25-year-old anime woman, consistent face and blue eyes, long midnight blue wavy hair with lavender tips, cat ear accessories, crescent moon hair clip, small star earrings. Detailed full-body portrait from head to shoes, centered, natural proportions, soft smile, crisp clean anime illustration, transparent background, no captions or text.

| Asset | Outfit and pose prompt |
| --- | --- |
| Morning | White cropped T-shirt, light denim shorts, white sneakers; relaxed standing pose, one hand near waist, warm smile |
| Afternoon | Black athletic crop top with lavender trim, charcoal running shorts with white piping, grey/white trainers; one hand on hip, the other making a light wave, playful confident smile |
| Evening | Short black wrap dress, burgundy sash, dark tights and black ankle boots; front standing pose with a soft smile and relaxed hands |
| Night | Navy short-sleeve silk sleep shirt with lavender piping, matching pajama shorts and fluffy lavender slippers; hands held gently near waist, cozy sleepy smile |

The night edit explicitly asked to keep the evening reference's face, hair, accessories and adult proportions unchanged. Every portrait requested transparent alpha and full head-to-toe framing. A 2160 × 3840 generation request did not produce native 4K, so the user approved local AI upscaling.

## 4K processing

Unmodified official Real-ESRGAN NCNN Vulkan with `realesr-animevideov3`, scale 4 and tile 256, ran locally on Intel UHD Graphics. Master portraits were fitted to transparent 2160 × 3840 canvases. Atlases were AI upscaled, split into nine tiles, alpha-trimmed and fitted to the same canvases. Final portrait WebP files use quality 94; expressions use quality 92. All 40 final `.webp` files are RGBA and exactly 2160 × 3840.

This is **AI upscaled 4K**. Upscaling improves edges and detail but does not recreate guaranteed native 4K detail, especially in the original smaller expression tiles.

## Motion

The bundled render uses Qt Quick breathing, subtle sway and crossfades. No fully rigged character, phoneme mouth animation or real Vidu-generated clips are claimed. Vidu generation and imported MP4/WebM clips are stored privately under `%LOCALAPPDATA%/LISA/motion`; they are excluded from the public source and packaged release. A generation prompt is built in `motion.py`, with a fixed camera, gentle natural motion, same character identity and a four-second loop request. Loop continuity depends on the generated result.

Upscaling source and license: https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan (MIT). Generated artwork is part of this LISA project; component licenses are listed in THIRD_PARTY_NOTICES.md.
