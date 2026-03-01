from tkinter import *
from tkinter.ttk import *
from tkinter import Label as Lab
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps, ImageGrab, ImageEnhance
from io import BytesIO
import win32clipboard
import os
from multiprocessing import Pool, freeze_support
from random import randint

def clean(text):
    while text.startswith(" "):
        text = text[1:]
    while text.endswith(" "):
        text = text[:-1]
    return text

def limit(i):
    if i<0:
        i = 0
    elif i>255:
        i = 255
    i = round(i)
    return i

def execute(tup):
    pixel, code = tup
    d = {"r": pixel[0],
         "g": pixel[1],
         "b": pixel[2],
         "a": pixel[3]}
    exec(code, d)
    return tuple([limit(d[i]) for i in "rgba"])

def point(image, code, master):
    image = image.convert("RGBA")
    pixels = tuple(image.getdata())
    pc = [(pixel,code) for pixel in pixels]
    pc_ = [pc[n:n+image.size[0]] for n in range(0,image.size[0]*image.size[1],image.size[0])]
    strip = Image.new("RGBA",(image.size[0],1))
    line = 0
    with Pool(4) as p:
        for pclet in pc_:
            new = p.map(execute, pclet)
            strip.putdata(tuple(new))
            image.paste(strip,(0,line))
            line+=1

            if line%20==0:
                master.image = master.original = image.copy()
                master.draw_image()
                master.onresize(None, True)
                master.update()
    #image.putdata(tuple(new))
    return image

def get_all_fonts():
    return [item for item in list(os.walk(r"C:\Windows\Fonts"))[-1][-1] if ".ttf" in item]

def get_bg(size):
    new_size = size[0]//8,size[1]//8
    image = Image.new("LA", new_size, (0,0))
    imload = image.load()
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            if y%2==1:
                imload[x,y] = (x%2*192, x%2*255)
            else:
                imload[x,y] = ((x+1)%2*192, (x+1)%2*255)
    return image.resize(size, Image.NEAREST).convert("RGBA")

def evaluate(variable):
    if not isinstance(variable, str):
        return variable
    try:
        out = eval(variable)
    except (NameError, SyntaxError):
        out = variable
    return out

def getsize(font, content):
    lines = content.split(r"\n")
    height = sum([font.getsize(i)[1] for i in lines])
    return (font.getsize(content.replace(r"\n","\n"))[0],round(height*1.2))

def inverter(image, pos):
    mask = Image.new("L", image.size)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(pos, outline = 255)
    inv = ImageOps.invert(image.convert("RGB"))
    image.paste(inv, (0,0), mask)
    return image

def send_to_clipboard(image):
    output = BytesIO()
    image.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def get_from_clipboard():
    obj = ImageGrab.grabclipboard()
    obj = Image.open(obj[0]) if isinstance(obj, list) else obj
    return obj.convert("RGBA")

def get_quality():
    l = list(range(10,101,5))
    ind = l.index(85)
    l.pop(ind)
    l.insert(ind,"!85")
    return l[::-1]

class GUI(Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = Menu(self)
        self.title("Pixel Image Editor v1.07d")
        self.minsize(400,200)
        self.iconbitmap("pie_logo_64.ico")
        self.history = []
        self.focus = 0
        self.path = ""
        self.mode = "crop"
        self.quality = 85
        self.optimize = True
        self.progressive = True
        self.selmode = False
        self.scaling = 1
        self.image = self.original = Image.new("RGB", (300,200), (255,255,255))
        self.tk.call("source", "sun-valley.tcl")
        self.tk.call("set_theme", "light")
        self.model = None#tf.keras.models.load_model("kfmodel2")
        self.is_dark = False
        
        self.filemenu = Menu(self.menu, tearoff=0)
        self.filemenu.add_command(label = "Open", command = self.open, accelerator="Ctrl+O")
        self.filemenu.add_command(label = "Save", command = self.save, accelerator="Ctrl+S")
        self.filemenu.add_command(label = "Configure", command = self.parameters)
        self.filemenu.add_command(label = "Remove EXIF", command = self.exif)
        self.menu.add_cascade(label = "File", menu = self.filemenu)

        self.hfilemenu = Menu(self.menu, tearoff=0)
        self.hfilemenu.add_command(label = "Undo", command = self.backward, accelerator="Ctrl+Z")
        self.hfilemenu.add_command(label = "Redo", command = self.forward, accelerator="Ctrl+Shift+Z")
        self.menu.add_cascade(label = "History", menu = self.hfilemenu)

        self.grmenu = Menu(self.menu, tearoff=0)

        self.ifilemenu = Menu(self.menu, tearoff=0)
        self.ifilemenu.add_command(label = "Resize", command = self.resize)
        self.ifilemenu.add_command(label = "Scale", command = self.thumbnail)
        self.ifilemenu.add_command(label = "Rotate", command = self.rotate)
        self.ifilemenu.add_command(label = "Expand", command = self.expand)
        self.ifilemenu.add_command(label = "Brightness", command = self.brightness)
        self.ifilemenu.add_command(label = "Contrast", command = self.contrast)
        self.ifilemenu.add_command(label = "Browse fonts", command = self.show_demo)
        self.ifilemenu.add_command(label = "Apply function", command = self.point)
        #self.filemenu.add_command(label = "kemono3x", command = self.kemono3x)
        self.grmenu.add_cascade(label = "Image", menu = self.ifilemenu)

        self.rfilemenu = Menu(self.menu, tearoff=0)
        self.rfilemenu.add_command(label = "Crop", command = self.crop)
        self.rfilemenu.add_command(label = "Paste", command = self.paste_over)
        self.rfilemenu.add_command(label = "Scaled paste", command = self.paste_over_scale)
        self.rfilemenu.add_command(label = "Add text", command = self.text)
        self.rfilemenu.add_command(label = "Add rich text", command = self.text2)
        self.rfilemenu.add_command(label = "Remove background", command = self.bg)
        self.rfilemenu.add_command(label = "Select", command = self.selection)
        self.grmenu.add_cascade(label = "Region", menu = self.rfilemenu)
        
        self.grmenu.add_separator()
        #self.filemenu = Menu(self.menu, tearoff=0)
        self.grmenu.add_command(label = "Resize", command = self.resize)
        self.grmenu.add_command(label = "Scale", command = self.thumbnail)
        self.grmenu.add_command(label = "Rotate", command = self.rotate)
        self.grmenu.add_command(label = "Expand", command = self.expand)
        self.grmenu.add_command(label = "Brightness", command = self.brightness)
        self.grmenu.add_command(label = "Contrast", command = self.contrast)
        self.grmenu.add_command(label = "Browse fonts", command = self.show_demo)
        self.grmenu.add_command(label = "Apply function", command = self.point)
        #self.grmenu.add_command(label = "kemono3x", command = self.kemono3x)
        self.grmenu.add_separator()
        self.grmenu.add_command(label = "Crop", command = self.crop)
        self.grmenu.add_command(label = "Paste", command = self.paste_over)
        self.grmenu.add_command(label = "Scaled paste", command = self.paste_over_scale)
        self.grmenu.add_command(label = "Add text", command = self.text)
        self.grmenu.add_command(label = "Add rich text", command = self.text2)
        self.grmenu.add_command(label = "Remove background", command = self.bg)
        self.grmenu.add_command(label = "Select", command = self.selection)

        self.menu.add_cascade(label = "Edit", menu = self.grmenu)

        self.setmenu = Menu(self.menu, tearoff=0)
        self.setmenu.add_command(label = "Coordinates", command = self.coords)
        self.setmenu.add_command(label = "Toggle Theme", command = self.theme)
        self.menu.add_cascade(label = "Settings", menu = self.setmenu)

        self.frame = Frame(self)
        self.frame.pack(fill = BOTH, expand = True)
        self.label = Canvas(self.frame, bg = "#ffffff")
        self.label.pack(fill = BOTH, expand = True, side = BOTTOM)

        self.coord_label = Label(self.frame, text = "x, y")

        self.config(menu = self.menu)
        self.label.bind("<Button-1>", self.onclick)
        self.label.bind("<ButtonRelease-1>", self.onrelease)
        self.label.bind("<Motion>", self.onmove)
        self.bind("<Control-o>", lambda e: self.open())
        self.bind("<Control-s>", lambda e: self.save())
        self.bind("<Control-c>", self.copy)
        self.bind("<Control-z>", lambda e: self.backward())
        self.bind("<Control-Shift-KeyPress-Z>", lambda e: self.forward())
        self.bind("<Control-v>", lambda e: self.open(True))
        self.label.bind("<Configure>", self.onresize)
        self.bind("<MouseWheel>", self.mwheel)

        self.oldsize = (0,0)
        self.after(1000, self.resize_manager)

        self.hor = ((0,0),(0,0),(0,0),(0,0),(255,255),(255,255),(255,255),(255,255),
                    (0,0),(0,0),(0,0),(0,0),(0,255),(0,255),(0,255),(0,255))*(128)
        self.horiz = Image.new("LA",(2048,1))
        self.horiz.putdata(self.hor)
        self.vert = Image.new("LA",(1,2048))
        self.vert.putdata(self.hor)
        self.horiz = self.horiz.convert("RGBA")
        self.vert = self.vert.convert("RGBA")
        self.drawn = []
        self.id = 0
        self.lens = 0
        self.coords_shown = False
        self.x_, self.y_ = 0, 0

        self.load_config()
        self.mainloop()

    def load_config(self):
        d = dict()
        if os.path.exists("config.txt"):
            with open("config.txt") as f:
                whole = f.read()
            for line in whole.split("\n"):
                if line:
                    key, prevalue = line.split(":",1)
                    value = clean(prevalue)
                    d[key] = eval(value)
            if "dark" in list(d.keys()):
                self.is_dark = not bool(d["dark"])
                self.theme()

    def theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.tk.call("set_theme", "dark")
            self.label.config(bg = "#222222")
        else:
            self.tk.call("set_theme", "light")
            self.label.config(bg = "#ffffff")
            self.menu.config(bg="#E7E7E7")
            self.setmenu.config(bg="#E7E7E7")
            self.grmenu.config(bg="#E7E7E7")
            self.filemenu.config(bg="#E7E7E7")
            self.ifilemenu.config(bg="#E7E7E7")
            self.hfilemenu.config(bg="#E7E7E7")
            self.rfilemenu.config(bg="#E7E7E7")

    def selection(self):
        Input(self, ["Point 1: ", "Point 2: "])
        self.xy1, self.xy2 = self.input
        
        self.draw_bars()

        self.xy1 = [round(self.xy1[0]/(self.image.size[0]/self.original.size[0])),
                    round(self.xy1[1]/(self.image.size[1]/self.original.size[1]))]
        self.xy2 = [round(self.xy2[0]/(self.image.size[0]/self.original.size[0])),
                    round(self.xy2[1]/(self.image.size[1]/self.original.size[1]))]

    def coords(self):
        if not self.coords_shown:
            self.label.pack_forget()#destroy()
            
            #self.label = Canvas(self.frame, bg = "#ffffff")
            #self.label.bind("<Button-1>", self.onclick)
            #self.label.bind("<ButtonRelease-1>", self.onrelease)
            #self.label.bind("<Motion>", self.onmove)
        
            #self.coord_label = Label(self.frame, text = "x, y")
            self.coord_label.pack(side = BOTTOM, anchor = SW, ipadx = 10)
            self.label.pack(fill = BOTH, expand = True, side = BOTTOM)
            self.coords_shown = True
        else:
            self.coord_label.pack_forget()
            self.coord_label.destroy()
            self.coord_label = Label(self.frame, text = "x, y")
            self.coords_shown = False

    def mwheel(self, event):
        if event.delta>0:
            self.lens+=1
        else:
            self.lens-=1
        if self.lens<=0:
            self.lens = -1
        self.onmove(event)

    def point(self):
        Input(self,["<code>"])

        self.original = self.image = point(self.original, self.input[0], self)
        self.hist(self.original,alt=True)
        self.focus+=1
        self.draw_image()
        self.onresize(None, True)

    def draw_image(self, render = True):
        #self.label.delete(ALL)
        if self.id and render:
            self.label.delete(self.id)
        if render:
            self.tkimage2 = ImageTk.PhotoImage(self.image)
            self.id = self.label.create_image(self.label.winfo_width()//2, self.label.winfo_height()//2, anchor=CENTER, image=self.tkimage2)
        for n in self.drawn:
            self.label.lift(n)
    def draw_bars(self):
        try:
            self.top = self.horiz.crop((0,0,abs(self.xy2[0]-self.xy1[0]),1))
            self.left = self.vert.crop((0,0,1,abs(self.xy2[1]-self.xy1[1])))
            self.tkimage_a = ImageTk.PhotoImage(self.top)
            self.tkimage_b = ImageTk.PhotoImage(self.left)
            self.tkimage_c = ImageTk.PhotoImage(self.top)
            self.tkimage_d = ImageTk.PhotoImage(self.left)

            xpad = self.label.winfo_width()//2-self.image.size[0]//2
            ypad = self.label.winfo_height()//2-self.image.size[1]//2

            xx = (self.xy1[0],self.xy2[0])
            xplus = self.coord_label.winfo_height() if self.original.size!=self.image.size else 0
            yplus = self.coord_label.winfo_height() if self.original.size!=self.image.size else 0
            yy = (self.xy1[1]+xplus,self.xy2[1]+yplus)

            #self.label.delete(ALL)
            while len(self.drawn)>4:
                self.label.delete(self.drawn.pop(0))
            #self.label.create_image(self.label.winfo_width()//2, self.label.winfo_height()//2, anchor=CENTER, image=self.tkimage)
            self.drawn.append( self.label.create_image(xpad+min(xx), ypad+min(yy), anchor=NW, image=self.tkimage_a) )
            self.drawn.append( self.label.create_image(xpad+max(xx), ypad+min(yy), anchor=NW, image=self.tkimage_b) )
            self.drawn.append( self.label.create_image(xpad+min(xx), ypad+max(yy), anchor=NW, image=self.tkimage_c) )
            self.drawn.append( self.label.create_image(xpad+min(xx), ypad+min(yy), anchor=NW, image=self.tkimage_d) )
        except Exception:
            pass

    def contrast(self):
        inp = Input(self, [("Scale,Contrast: ", "0.0,5.0")])
        image = self.original.copy()
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.input[0])
        self.original = self.image = image.copy()
        self.hist(self.original,alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def brightness(self):
        inp = Input(self, [("Scale,Brightness: ", "0.0,5.0")])
        image = self.original.copy()
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.input[0])
        self.original = self.image = image.copy()
        self.hist(self.original,alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def paste_over(self):
        overlay = get_from_clipboard()
        overlay = overlay.resize((abs(self.xy1[0]-self.xy2[0]),abs(self.xy1[1]-self.xy2[1])), Image.BICUBIC)#(*self.xy1,*self.xy2)
        bg = self.original.copy()
        mx = self.xy1[0] if self.xy1[0]<self.xy2[0] else self.xy2[0]
        my = self.xy1[1] if self.xy1[1]<self.xy2[1] else self.xy2[1]
        bg.paste(overlay,(mx,my), overlay)
        self.original = self.image = bg.copy()
        self.hist(self.original,alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def paste_over_scale(self):
        overlay = get_from_clipboard()
        overlay.thumbnail((abs(self.xy1[0]-self.xy2[0]),abs(self.xy1[1]-self.xy2[1])), Image.BICUBIC)#(*self.xy1,*self.xy2)
        bg = self.original.copy()
        mx = self.xy1[0] if self.xy1[0]<self.xy2[0] else self.xy2[0]
        my = self.xy1[1] if self.xy1[1]<self.xy2[1] else self.xy2[1]
        bg.paste(overlay,(mx,my), overlay)
        self.original = self.image = bg.copy()
        self.hist(self.original,alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def resize_manager(self):
        if not self.selmode:
            x, y = self.winfo_width(), self.winfo_height()
            if self.oldsize!=(x,y):
                self.onresize(None, True)
                self.oldsize = (x,y)
        self.after(1000, self.resize_manager)

    def onresize(self, event, force = False, render = True):#CHANGED IN 12
        if not randint(0, 10) or force:
            while len(self.drawn)>0:
                self.label.delete(self.drawn.pop(0))
            x, y = self.winfo_width(), self.winfo_height()
            self.scaling = min([x/self.original.size[0], y/self.original.size[1]])
            
            self.image = self.original.copy()
            self.image.thumbnail((x,y))
            self.draw_image(render = render)#.label.winfo_width()//2, self.label.winfo_height()//2, anchor=CENTER, image=self.tkimage)#self.label.config(image = self.tkimage)
        
    def copy(self, event):
        send_to_clipboard(self.original)
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)

    def expand(self):
        inp = Input(self, [("Top: ",0),("Left: ",0),("Right: ",0),("Bottom: ",0),"Color: "])
        t,l,r,b,c = self.input
        bg = Image.new("RGBA", (self.original.size[0]+l+r, self.original.size[1]+t+b), c)
        bg.paste(self.original,(l,t))
        self.image = self.original = bg.copy()
        self.hist(self.original,alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def rotate(self):
        inp = Input(self, ["Degrees: ",("Expand: ",[True,False])])
        deg, exp = self.input
        self.original = self.original.rotate(deg, expand = exp)
        self.hist(self.original)
        self.focus+=1
        self.image = self.original.copy()
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def text(self):
        inp = Input(self, [("Font file: ",get_all_fonts()),"Text: "])
        fontname, content = self.input
        font = ImageFont.truetype(fontname, size = 72)
        size = getsize(font,content)#font.getsize(content)
        #size = (size[0],size[1]*((content.count(r"\n"))+1))
        overlay = Image.new("RGBA", size)
        draw = ImageDraw.Draw(overlay)
        draw.multiline_text(text=content.replace(r"\n","\n"), xy=(0,0), fill=(0,0,0), font=font)
        overlay = overlay.crop(overlay.getbbox())
        overlay = overlay.resize((abs(self.xy2[0]-self.xy1[0]),abs(self.xy2[1]-self.xy1[1])), Image.BICUBIC)
        self.original.paste(overlay, self.xy1, overlay)
        self.hist(self.original)
        self.focus+=1
        self.image = self.original.copy()
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def text2(self):
        inp = Input(self, [("Font file: ",get_all_fonts()),"Text: ","Fill color: ","Stroke: ","Stroke fill: "])
        fontname, content, color, sw, sf = self.input
        font = ImageFont.truetype(fontname, size = 72)
        size = (getsize(font,content)[0]+20,getsize(font,content)[1]+20)#font.getsize(content)
        #size = (size[0],size[1]*((content.count(r"\n"))+1))
        overlay = Image.new("RGBA", size)
        draw = ImageDraw.Draw(overlay)
        draw.multiline_text(text=content.replace(r"\n","\n"), xy=(10,10), fill=color, stroke_width=sw, stroke_fill=sf, font=font)
        overlay = overlay.crop(overlay.getbbox())
        overlay = overlay.resize((abs(self.xy2[0]-self.xy1[0]),abs(self.xy2[1]-self.xy1[1])), Image.BICUBIC)
        self.original.paste(overlay, self.xy1, overlay)
        self.hist(self.original)
        self.focus+=1
        self.image = self.original.copy()
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def open(self, fromram = False):
        while self.drawn:
            self.label.delete(self.drawn.pop(0))
        if not fromram:
            self.path = askopenfilename()
            self.original = self.image = Image.open(self.path).convert("RGBA")
        else:
            self.original = self.image = get_from_clipboard()
        self.hist(self.image)
        self.focus = len(self.history)-1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        #self.label.config(image = self.tkimage)
        #self.label.delete(ALL)
        self.draw_image()#self.label.create_image(self.label.winfo_width()//2, self.label.winfo_height()//2, anchor=CENTER, image=self.tkimage)
        self.onresize(None, True)

    def save(self):
        files = [('All Files', '*.*'), 
                 ('Portable Network Graphics', '*.png'),
                 ('Joint Photographic Experts Group', '*.jpg'),
                 ('Windows Icon File', '*.ico'),
                 ('Web Picture Format', '*.webp'),
                 ('Bitmap Image', '*.bmp'),
                 ('Graphics Interchange Format', '*.gif')]
        f = asksaveasfile(filetypes = files, defaultextension = files)
        name = f.name
        f.close()
        ext = name.rsplit(".",1)[-1].lower()
        
        if ext in ["png","webp","ico","bmp"]:
            self.original.save(name, quality = self.quality, optimize = self.optimize, progressive = self.progressive)
        elif ext=="gif":
            self.original.convert("P", dither=Image.Dither.FLOYDSTEINBERG, palette=Image.Palette.ADAPTIVE).save(name, quality = self.quality, optimize = self.optimize, progressive = self.progressive)
        else:
            self.original.convert("RGB").save(name, quality = self.quality, optimize = self.optimize, progressive = self.progressive)

    def parameters(self):
        inp = Input(self, [("Quality: ",get_quality()),("Optimize: ",[True,False]),("Progressive: ",[True,False])])
        self.quality,self.optimize,self.progressive = self.input
        
    def hist(self, image="", alt=False):
        self.history = self.history[:self.focus+1] if self.history and alt else self.history
        if image: self.history.append(image.copy())
        print(len(self.history))

    def forward(self):
        self.focus+=1
        self.hist()
        self.original = self.image = self.history[self.focus]
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def backward(self):
        self.focus-=1
        self.original = self.image = self.history[self.focus]
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        print(self.focus, len(self.history))
        self.onresize(None, True)

    def onclick(self, event):
        self.selmode = True
        self.image = self.original.copy()
        self.onresize(None, force=True)
        x,y = event.x,event.y
        self.xy1 = (x-abs(self.image.size[0]-self.label.winfo_width())//2,y-abs(self.image.size[1]-self.label.winfo_height())//2)
        self.draw_image()

    def onrelease(self, event):
        x,y = event.x,event.y
        self.xy2 = (x-abs(self.image.size[0]-self.label.winfo_width())//2,y-abs(self.image.size[1]-self.label.winfo_height())//2)
        #draw = ImageDraw.Draw(self.image)
        #draw.rectangle([self.xy1,self.xy2], outline = (0,0,0))
        self.image = self.original.copy()
        self.onresize(None, force=True)
        #self.image = inverter(self.image, [self.xy1,self.xy2])
        #self.hist(self.image)
        #self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        #self.label.config(image = self.tkimage)
        
        self.selmode = False

        #self.draw_bars()
        
        self.xy1 = [round(self.xy1[0]/(self.image.size[0]/self.original.size[0])),
                    round(self.xy1[1]/(self.image.size[1]/self.original.size[1]))]
        self.xy2 = [round(self.xy2[0]/(self.image.size[0]/self.original.size[0])),
                    round(self.xy2[1]/(self.image.size[1]/self.original.size[1]))]
        if self.xy2[0]<self.xy1[0]:
            self.xy2[0],self.xy1[0] = self.xy1[0],self.xy2[0]
        if self.xy2[1]<self.xy1[1]:
            self.xy2[1],self.xy1[1] = self.xy1[1],self.xy2[1]

        if self.xy1[0]<0:
            self.xy1[0] = 0
        if self.xy1[1]<0:
            self.xy1[1] = 0
        if self.xy2[0]>=self.original.size[0]:
            self.xy2[0] = self.original.size[0]-1
        if self.xy2[1]>=self.original.size[1]:
            self.xy2[1] = self.original.size[1]-1

        self.xy1 = [round(self.xy1[0]*(self.image.size[0]/self.original.size[0])),
                    round(self.xy1[1]*(self.image.size[1]/self.original.size[1]))]
        self.xy2 = [round(self.xy2[0]*(self.image.size[0]/self.original.size[0])),
                    round(self.xy2[1]*(self.image.size[1]/self.original.size[1]))]
        
        self.draw_bars()

        self.xy1 = [round(self.xy1[0]/(self.image.size[0]/self.original.size[0])),
                    round(self.xy1[1]/(self.image.size[1]/self.original.size[1]))]
        self.xy2 = [round(self.xy2[0]/(self.image.size[0]/self.original.size[0])),
                    round(self.xy2[1]/(self.image.size[1]/self.original.size[1]))]
        if self.image.size!=self.original.size:
            self.xy1[1]+=round(self.coord_label.winfo_height()/(self.image.size[0]/self.original.size[0]))
            self.xy2[1]+=round(self.coord_label.winfo_height()/(self.image.size[0]/self.original.size[0]))


    def onmove(self, event):
        if self.coords_shown:
            x,y = event.x,event.y
            x, y = (x-abs(self.image.size[0]-self.label.winfo_width())//2,y-abs(self.image.size[1]-self.label.winfo_height())//2)
            self.x_ = round(x/(self.image.size[0]/self.original.size[0]))
            self.y_ = round(y/(self.image.size[1]/self.original.size[1]))
            self.coord_label.config(text = f"{self.x_}, {self.y_}")
        if self.lens==-1:
            self.onresize(None, force = True, render = True)
            self.lens = 0
        if not self.lens:
            if self.selmode:# and not randint(0,10):
                x,y = event.x,event.y
                self.xy2 = (x-abs(self.image.size[0]-self.label.winfo_width())//2,y-abs(self.image.size[1]-self.label.winfo_height())//2)
                
                self.image = self.original.copy()
                self.onresize(None, force = True, render = False) #NEW IN 12
                
                self.draw_bars()
                self.update()
        else:
            magnify = 1.0 + (self.lens-1)/4
            w, h = self.label.winfo_width()/magnify, self.label.winfo_height()/magnify
            x, y = int(event.x/self.label.winfo_width()*self.original.size[0]-w/2), int(event.y/self.label.winfo_height()*self.original.size[1]-h/2)
            self.image = self.original.crop((x,y,x+w,y+h)).resize((self.label.winfo_width(),self.label.winfo_height()), Image.Resampling.BICUBIC)
            self.draw_image()

    def crop(self):
        self.original = self.image = self.original.crop((*self.xy1,*self.xy2))
        self.hist(self.original,alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def resize(self):
        inp = Input(self, [("X: ", self.original.size[0]),("Y: ", self.original.size[1]),("Method: ",["Nearest","Bilinear","!Bicubic"])])
        
        if self.input[2].lower()=="bicubic":
            self.input[2] = Image.BICUBIC
        elif self.input[2].lower()=="bilinear":
            self.input[2] = Image.BILINEAR
        elif self.input[2].lower()=="nearest":
            self.input[2] = Image.NEAREST
            
        self.original = self.image = self.original.resize((self.input[0],self.input[1]), self.input[2])
        self.hist(self.original, alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def thumbnail(self):
        inp = Input(self, [("X: ", self.original.size[0]),("Y: ", self.original.size[1]),("Method: ",["Nearest","Bilinear","!Bicubic"])])
        if self.input[2].lower()=="bicubic":
            self.input[2] = Image.BICUBIC
        elif self.input[2].lower()=="bilinear":
            self.input[2] = Image.BILINEAR
        elif self.input[2].lower()=="nearest":
            self.input[2] = Image.NEAREST
        self.original.thumbnail((self.input[0],self.input[1]), self.input[2])
        self.original = self.image = self.original
        self.hist(self.original, alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        #self.geometry(f"{self.image.size[0]}x{self.image.size[1]}")
        self.onresize(None, True)

    def exif(self):
        empty = Image.new("RGBA", self.image.size)
        empty.putdata(self.original.getdata())
        self.original = empty.copy()
        self.onresize(None, True)

    def bg(self):
        new = self.original.copy().resize(tuple([2*i for i in self.original.size]), Image.BICUBIC)
        inp = Input(self, ["Thresh: "])
        ImageDraw.floodfill(new, (self.xy1[0]+self.xy2[0],self.xy1[1]+self.xy2[1]), (0,0,0,0), thresh=self.input[0])
        self.image = self.original = new.resize(self.original.size, Image.BICUBIC)
        self.hist(self.original, alt=True)
        self.focus+=1
        #self.tkimage = ImageTk.PhotoImage(self.image)
        self.draw_image()#self.label.config(image = self.tkimage)
        self.onresize(None, True)

    def show_demo(self):
        self.demo = FontDemo(self, self.is_dark)
        
                

class Input(Toplevel):
    def __init__(self, master, labels, **kwargs):
        super().__init__(**kwargs)
        self.iconbitmap("pie_logo_64.ico")
        frames = []
        self.master = master
        self.variables = []
        self.labels_ = []
        self.entries = []
        self.master.input = []
        frames.append(Frame(self))
        self.display = False
        self.mode = None
        for num, label in enumerate(labels):
            if isinstance(label,str):
                if "<code>" in label:
                    self.labels_.append(Label(frames[-1], text = "Code: "))
                    self.entries.append(Text(frames[-1]))
                    self.mode = "code"
                else:
                    self.labels_.append(Label(frames[-1], text = label))#, font = "Callibri 10"))
                    self.variables.append(StringVar())
                    self.entries.append(Entry(frames[-1], textvariable = self.variables[-1]))#, font = "Callibri 12"))
            elif "Scale," in label[0]:
                self.display = True
                label, value = label
                label = label.replace("Scale,","",1)
                self.mode = "brightness" if "brightness" in label.lower() else "contrast"
                self.labels_.append(Label(frames[-1], text = label))#, font = "Callibri 10"))
                self.variables.append(DoubleVar(value = 1.0))
                self.entries.append(Scale(frames[-1], command = self.on_scale, variable = self.variables[-1], from_ = eval(value.split(",")[0]), to = eval(value.split(",")[1])))
            elif not (isinstance(label[1], list) or isinstance(label[1], tuple)):
                self.labels_.append(Label(frames[-1], text = label[0]))#, font = "Callibri 10"))
                self.variables.append(StringVar(value = str(label[1])))
                self.entries.append(Entry(frames[-1], textvariable = self.variables[-1]))#, font = "Callibri 12"))
            else:
                label, value = label
                self.labels_.append(Label(frames[-1], text = label))#, font = "Callibri 10"))
                self.variables.append(StringVar())
                if True in ["!" in str(v) for v in value]:
                    self.variables[-1].set([v for v in value if "!" in str(v)][0].replace("!",""))
                    value = [str(v).replace("!","") for v in value]
                self.entries.append(Combobox(frames[-1], textvariable = self.variables[-1], values = value))#, font = "Callibri 12"))

            self.labels_[-1].grid(column = 0, row = num)
            if "?" in label:
                self.labels_[-1].config(text = label.replace("?",""))
                self.question = Button(frames[-1], text = "?", width = 2, command = self.on_button)
                self.question.num = num
                self.question.grid(column = 1, row = num, sticky = E, padx = (0,10))
            self.entries[-1].grid(column = 1, row = num, padx = (0,10), sticky = EW)
        frames[-1].pack(expand = True, fill = BOTH)
        frames[-1].columnconfigure(1, weight = 1)

        if self.display:
            self.image = self.master.original.copy()
            self.image.thumbnail((200,200))
            self.tkimage = ImageTk.PhotoImage(self.image)
            self.screen = Lab(self, image = self.tkimage)
            self.screen.pack(fill = BOTH, expand = True)
        print(self.display)

        okay = Button(self, text = "Ok", command = self.onpress)
        okay.pack()
        self.bind("<Shift-Return>", self.onpress)
        self.mainloop()

    def on_scale(self, value):
        self.image = self.master.original.copy()
        self.image.thumbnail((200,200))
        enhancer = ImageEnhance.Brightness(self.image) if self.mode=="brightness" else ImageEnhance.Contrast(self.image)
        self.imagenew = enhancer.enhance(eval(value))
        self.tkimage = ImageTk.PhotoImage(self.imagenew)
        self.screen.config(image = self.tkimage)

    def onpress(self, event=None):
        if not self.mode=="code":
            self.master.input = [evaluate(i.get()) for i in self.variables]
        else:
            self.master.input = [self.entries[0].get("1.0",END)]
        self.quit()
        self.destroy()

    def on_button(self):
        self.variables[self.question.num].set(askopenfilename())
        self.focus_set()

class FontDemo(Toplevel):
    def __init__(self, master, darkmode, **kwargs):
        super().__init__(**kwargs)
        self.iconbitmap("pie_logo_64.ico")
        self.master = master
        self.darkmode = darkmode
        self.menuvar = StringVar()
        self.menuvar.set(get_all_fonts()[0])
        self.menuvar.trace("w", lambda name, index, mode, sv=self.menuvar: self.callback(sv))
        self.menu = ttk.Combobox(self, textvariable=self.menuvar, values=get_all_fonts())
        self.label = Label(self)

        self.menu.pack(fill=X)
        self.label.pack(fill=BOTH, expand=True)
        self.callback()

    def callback(self, event=None):
        self.image = Image.new("RGBA",(500,250), (0,0,0,0))
        font = ImageFont.truetype(self.menuvar.get(), size = 72)
        draw = ImageDraw.Draw(self.image)
        color = (1,1,1,255) if not self.darkmode else (254,254,254,255)
        draw.text(xy = (10,10), text = self.menuvar.get(), fill=color, font=font)
        x1,y1,x2,y2 = self.image.convert("RGB").getbbox()
        self.image = self.image.crop((x1-10,y1-10,x2+10,y2+10))
        self.tkimage = ImageTk.PhotoImage(self.image)
        self.label.config(image = self.tkimage)


if __name__=="__main__":
    freeze_support()
    import ctypes
    try:
        # Windows 8.1 and later
        ctypes.windll.shcore.SetProcessDpiAwareness(2) 
    except AttributeError:
        try:
            # Windows 7
            ctypes.windll.user32.SetProcessDPIAware()
        except AttributeError:
            pass
    gui = GUI()
