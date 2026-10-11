# Artwork and motion provenance

The application logo uses the user's supplied `lisa.jpg` (October 3, 2026), preserving the complete artwork. `assets/lisa-logo.jpg` is an unchanged copy of the supplied 1254 × 1254 JPEG; `assets/lisa.ico` includes Windows icon sizes from 16 × 16 through 256 × 256. Both Windows bundle specifications include the display logo. The executable, installer, taskbar and shortcuts use this ICO; the app header uses the JPEG.

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

## Motion through 1.9.2

The bundled render uses Qt Quick breathing, subtle sway and crossfades. No fully rigged character, phoneme mouth animation or real Vidu-generated clips are claimed. Vidu generation and imported MP4/WebM clips are stored privately under `%LOCALAPPDATA%/LISA/motion`; they are excluded from the public source and packaged release. A generation prompt is built in `motion.py`, with a fixed camera, gentle natural motion, same character identity and a four-second loop request. Loop continuity depends on the generated result.

Upscaling source and license: https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan (MIT). Generated artwork is part of this LISA project; component licenses are listed in THIRD_PARTY_NOTICES.md.

## Immersive scene and custom portrait rig, 1.10.0

On October 9, 2026 the built-in imagegen tool created `assets/scenes/moonlit-room.png` and edited the evening master into `assets/avatar/blink.png` and `talk.png`, preserving its composition and transparent background. Exact prompts and roles are in `assets/art-generation-1.10.json`. The background is approximately 1672 × 941; the two face-state frames approximately 941 × 1672. They are not claimed to be native 4K assets. All four master portraits share the registered face position; shaders blend only local eye/mouth regions, leaving outfit artwork intact.

`assets/avatar/rig.json` records the normalized overlay anchors. `ui/Avatar.qml` drives independent blink, mouth, head, nod and hair deformation controls. The mouth uses the current playback RMS envelope, with smoothing; waiting for a voice response does not move the mouth. The custom 2D texture rig is not an exported Cubism model or a skinned VRM/3D mesh, and does not infer phonemes or independent skeletal body actions. Original illustrated poses remain available. `tools/compile_shaders.py` creates shader packages for the supported graphics backends during builds.

The user's Ani reference video was inspected locally for visual interaction and interface behavior. It is not bundled, reused as Lisa footage, uploaded to a provider or included in the public repository. Vidu and imported clips remain private local data. Green-screen removal is optional per clip; older cache entries default to unkeyed playback.

## Interactive red-haired suite, October 11, 2026

The user supplied outputs.zip with 142 painted poses and 31 reference/animatic sequences. It contains no deformable model. The local Blender rig has 52 bones, 48 skeletal clips and five facial controls; compatible mesh parts are combined into 33 mesh objects. Original expression and clothing reference textures are used unchanged. The editable blend, build and optimization scripts accompany the source archive.

The built-in image generation tool removed the background from C-T01-P01.webp to create assets/suite/references/lisa-standing-approved.png. Prompt: Remove only the gray background; preserve the adult red-haired Lisa, face, wavy hair, black ribbed crop top, belt, pleated skirt, sandals and pose; full character in frame; transparent background; no text or added objects. The output is 767 by 2051 pixels and has not been represented as native 4K. It supplies controlled frontal idle appearance, with subtle runtime eye/mouth/breathing deformation. Walking and turning use skeletal 3D, whose complete production likeness remains unfinished.
