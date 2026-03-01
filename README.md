
# Pixel Image Editor
**PIE** is a simple image editor written in Python using tkinter and Pillow. It has tools similar to Photoshop/Krita while keeping the simplicity of MS Paint. The editor is intended for Windows and some features depend on the platform.
![PIE Screenshot](/pie-scr.png)
## Main Functionality
The editor allows changing the image as a whole or a selected region. PIE also has a zoom mode where one can inspect the pixels more closely. To do so use the mouse wheel.
A variety of output formats are supported, to set their settings go to File/Configure, most of the settings apply to lossy formats in here.
Setting expressions instead of values in fields is allowed. Referencing colors can be done by either hex values (#ff0000) or color names, such as "red".
## The Config File
Also known as `config.txt`, as of now it controls the setting of the dark theme on program start. Change the value to either `True` or `False` to enable/disable dark theme mode. Dark mode can be toggled from the interface as well.
## Supported Shortcuts
The program supports Undo (Ctrl+Z) and Redo (Ctrl+Shift+Z) actions and has a clipboard. One can also copy a file or an image via Ctrl+C and paste it into the editor via Ctrl+V. To copy the whole image as an image object, use Ctrl+C within the main window.
## Custom Filters
The **Apply Function** option allows one to change the `r`, `g`, `b`, `a` variables using a common script for all pixels. Example: paste the following code to make the image twice as dark.
```
r,g,b = r//2,g//2,b//2
```
I tried to avoid including numpy as a dependency, so processing all pixels takes time depending on image size. For demonstration purposes it's good enough.

> Written with [StackEdit](https://stackedit.io/).