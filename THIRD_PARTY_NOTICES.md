LISA uses unmodified PySide6 / Qt 6.10.2, Python, Pillow, NumPy, sounddevice / PortAudio, FFmpeg through Qt Multimedia, and the PyInstaller bootloader. Their original licenses apply to those components. LISA's source license does not replace them.

- PySide6 / Qt: https://doc.qt.io/qtforpython-6/licenses.html and https://www.qt.io/licensing/open-source-lgpl-obligations
- Qt source: https://download.qt.io/archive/qt/6.10/6.10.2/ and https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.10.2
- Python: https://docs.python.org/3/license.html
- Pillow: https://github.com/python-pillow/Pillow/blob/main/LICENSE
- NumPy: https://github.com/numpy/numpy/blob/main/LICENSE.txt
- sounddevice / PortAudio: https://github.com/spatialaudio/python-sounddevice/blob/master/LICENSE and https://www.portaudio.com/license.html
- FFmpeg: https://ffmpeg.org/legal.html
- PyInstaller: https://pyinstaller.org/en/stable/license.html

Qt libraries are loaded as separate DLLs, extracted at runtime by the one-file package. The build script and public source allow rebuilding the app using replacement compatible libraries; no restrictions are imposed on modifying those components or debugging such changes. Vendor license notices are included under `licenses/` inside the bundle and source repository.

Artwork was generated with the built-in OpenAI image generation tool from the user's selected LISA references, then upscaled offline with unmodified Real-ESRGAN NCNN Vulkan using realesr-animevideov3. Upscaling tool: https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan (MIT). It is a production tool and is not included in LISA.exe. Artwork provenance and prompt details: ASSETS.md.
