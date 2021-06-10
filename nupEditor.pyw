import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import struct
import io

class nupEditor:
    def __init__(self, window):
        window.title("nupEditor")
        window.bind("<B1-Motion>", self.moveTextureEvent)
        self.currentTexture = None
        self.menuBar = tk.Menu(window)
        self.menuBar.add_command(label = "Open Nup", command = lambda: self.openNup())
        self.menuBar.add_command(label = "Save Nup", state = "disabled", command = lambda: self.saveNup())
        self.menuBar.add_command(label = "Replace Texture", state = "disabled", command = lambda: self.replaceTexture())
        self.menuBar.add_command(label = "Save Texture", state = "disabled", command = lambda: self.saveTexture())
        window.config(menu = self.menuBar)
        self.textureFrame = tk.LabelFrame(window, borderwidth = 0, highlightthickness = 0)
        self.textureFrame.grid(row = 0, column = 0, sticky = "NW")
        self.listLabel = tk.Label(self.textureFrame, text = "Select Texture: ")
        self.listLabel.grid(row = 0, column = 0, sticky = 'W')
        self.listNumber = tk.StringVar()
        self.listDropDown = ttk.Combobox(self.textureFrame, width = 4, textvariable = self.listNumber)
        self.listDropDown["values"]
        self.listDropDown.grid(row = 0, column = 1)
        self.listDropDown.bind("<<ComboboxSelected>>", self.loadTextureEvent)
        self.textureInfoFrame = tk.LabelFrame(self.textureFrame, relief = "sunken")
        self.textureInfoFrame.grid(row = 1, column = 0, columnspan = 2, sticky = "WE")
        self.heightLabel = tk.Label(self.textureInfoFrame, text = "Height: ")
        self.heightLabel.grid(row = 0, column = 0, sticky= 'W')
        self.widthLabel = tk.Label(self.textureInfoFrame, text = "Width: ")
        self.widthLabel.grid(row = 1, column = 0, sticky = 'W')
        self.mipsLabel = tk.Label(self.textureInfoFrame, text = "Mips: ")
        self.mipsLabel.grid(row = 2, column = 0, sticky = 'W')
        self.typeLabel = tk.Label(self.textureInfoFrame, text = "Type: ")
        self.typeLabel.grid(row = 3, column = 0, sticky = 'W')
        self.addressLabel = tk.Label(self.textureInfoFrame, text = "Address: ")
        self.addressLabel.grid(row = 4, column = 0, sticky = 'W')
        self.canvasFrame = tk.LabelFrame(window, relief = "sunken")
        self.canvasFrame.grid(row = 0, column = 1)
        self.textureCanvas = tk.Canvas(self.canvasFrame, bg = "gray", highlightthickness = 0, height = 522, width = 522)
        self.textureCanvas.grid(row = 0, column = 0)

    def clearData(self):
        self.fb = io.BytesIO()
        self.currentTexture = None
        self.listDropDown.set("")
        self.listDropDown["values"] = []
        self.heightLabel.config(text = "Height: ")
        self.widthLabel.config(text = "Width: ")
        self.mipsLabel.config(text = "Mips: ")
        self.typeLabel.config(text = "Type: ")
        self.addressLabel.config(text = "Address: ")
        self.textureCanvas.delete("all")
        self.menuBar.entryconfig("Save Nup", state = "disabled")
        self.menuBar.entryconfig("Replace Texture", state = "disabled")
        self.menuBar.entryconfig("Save Texture", state = "disabled")

    def openNup(self):
        try:
            name = filedialog.askopenfilename(filetypes = (("Bionicle Heroes NU20", "*.nup"), ("All Files", "*.*")))
            f = open(name, "rb")
            magic = struct.unpack('I', f.read(4))[0]
            if magic != 0x3032554E:
                msgBox = messagebox.showerror("Error", "Selected file is not a NUP archive! It will not be loaded!")
                f.close()
                self.clearData()
            else:
                f.seek(0x00, os.SEEK_SET)
                fileBytes = f.read()
                f.close()
                self.loadNup(fileBytes)
        except FileNotFoundError:
            pass

    def linearScan(self, filePointer):
        sFlag = False
        theSize = self.getFileSize(filePointer)
        fileSizeDiv = theSize // 0x04
        for i in range(0, fileSizeDiv):
            scan = struct.unpack('I', filePointer.read(4))[0]
            if scan == 0x30545354:
                index = filePointer.tell()
                sFlag = True
                break
        if sFlag == True:
            return index
        else:
            return None

    def getFileSize(self, filePointer):
        filePointer.seek(0x00, os.SEEK_END)
        fileSize = filePointer.tell()
        filePointer.seek(0x00, os.SEEK_SET)
        return fileSize

    def loadNup(self, fileBytes):
        self.fb = io.BytesIO(fileBytes)
        self.indexLocation = self.linearScan(self.fb)
        if self.indexLocation is None:
            msgBox = messagebox.showerror("Error", "Texture index not found in NUP archive!")
            self.clearData()
        else:
            self.fb.seek(self.indexLocation, os.SEEK_SET)
            fullSize = struct.unpack('I', self.fb.read(4))[0]
            self.indexCount = struct.unpack('I', self.fb.read(4))[0]
            if self.indexCount == 0x00:
                msgBox = messagebox.showerror("Error", "No textures in index!")
                self.clearData()
            else:
                self.fb.seek(0x08, os.SEEK_CUR)
                self.indexSize = struct.unpack('I', self.fb.read(4))[0]
                self.fb.seek(0x08, os.SEEK_CUR)
                self.entryList = []
                self.imageList = []
                imageListCount = []
                for i in range(0, self.indexCount):
                    entryLocation = self.fb.tell()
                    entryWidth = struct.unpack('I', self.fb.read(4))[0]
                    entryHeight = struct.unpack('I', self.fb.read(4))[0]
                    entryMips = struct.unpack('I', self.fb.read(4))[0]
                    self.fb.seek(0x04, os.SEEK_CUR)
                    entryAddress = struct.unpack('I', self.fb.read(4))[0]
                    if ((entryWidth != 0x00) and (entryHeight != 0x00)):
                        self.entryList.append(entryLocation)
                        self.imageList.append(entryAddress)
                # enable the menuBar options
                self.menuBar.entryconfig("Save Nup", state = "active")
                self.menuBar.entryconfig("Replace Texture", state = "active")
                self.menuBar.entryconfig("Save Texture", state = "active")
                # Init the dropdown
                for i in range(0, len(self.imageList)):
                    imageListCount.append(i + 1)
                self.listDropDown["values"] = imageListCount
                self.listDropDown.current(0)
                self.loadTexture()

    def loadTexture(self):
        self.ddsEntry = self.entryList[int(self.listDropDown.get()) - 1]
        self.ddsLocation = self.imageList[int(self.listDropDown.get()) - 1] + self.indexLocation + self.indexSize + 0x04
        self.fb.seek(self.ddsLocation, os.SEEK_SET)
        self.fb.seek(0x0C, os.SEEK_CUR)
        ddsHeight = struct.unpack('I', self.fb.read(4))[0]
        ddsWidth = struct.unpack('I', self.fb.read(4))[0]
        self.fb.seek(0x08, os.SEEK_CUR)
        ddsMips = struct.unpack('I', self.fb.read(4))[0]
        self.fb.seek(0x34, os.SEEK_CUR)
        ddsType = self.fb.read(0x04).decode()
        self.fb.seek(-0x58, os.SEEK_CUR)
        self.heightLabel.config(text = "Height: " + str(ddsHeight))
        self.widthLabel.config(text = "Width: " + str(ddsWidth))
        self.mipsLabel.config(text = "Mips: " + str(ddsMips))
        self.typeLabel.config(text = "Type: " + str(ddsType))
        self.addressLabel.config(text = "Address: " + str(hex(self.ddsLocation)))
        if ddsMips == 0x00:
            self.currentSize = (ddsWidth * ddsHeight * 0x06 ) + 0x80
        else:
            self.currentSize = (ddsWidth * ddsHeight) + 0x80
            for i in range(1, ddsMips):
                ddsHeight //= 0x02
                ddsWidth //= 0x02
                self.currentSize += max(0x01, ((ddsWidth + 0x03) // 0x04)) * max(0x01, ((ddsHeight + 0x03) // 0x04)) * 0x10
        dds = self.fb.read(self.currentSize)
        self.currentTexture = Image.open(io.BytesIO(dds))
        self.currentTexture = ImageTk.PhotoImage(self.currentTexture)
        self.textureCanvas.create_image(int(self.textureCanvas.winfo_width()) // 2, int(self.textureCanvas.winfo_height()) // 2, image = self.currentTexture)

    def loadTextureEvent(self, event):
        self.loadTexture()

    def moveTextureEvent(self, event):
        if self.currentTexture is not None:
            self.textureCanvas.delete("all")
            self.textureCanvas.create_image(event.x, event.y, image = self.currentTexture)

    def saveNup(self):
        try:
            saveNupName = filedialog.asksaveasfile(mode = "wb", defaultextension = ".nup", filetypes = (("Bionicle Heroes NU20", "*.nup"), ("All Files", "*.*")))
            self.fb.seek(0x00, os.SEEK_SET)
            fileBytes = self.fb.read()
            saveNupName.write(fileBytes)
            saveNupName.close()
        except AttributeError:
            pass

    def saveTexture(self):
        try:
            saveTextureName = filedialog.asksaveasfile(mode = "wb", defaultextension = ".dds", filetypes = (("DDS image", "*.dds"), ("All Files", "*.*")))
            self.fb.seek(self.ddsLocation, os.SEEK_SET)
            fileBytes = self.fb.read(self.currentSize)
            saveTextureName.write(fileBytes)
            saveTextureName.close()
        except AttributeError:
            pass

    def replaceTexture(self):
        try:
            name = filedialog.askopenfilename(filetypes = (("DDS image", "*.dds"), ("All Files", "*.*")))
            f = open(name, "rb")
            magic = struct.unpack('I', f.read(4))[0]
            if magic != 0x20534444:
                msgBox = messagebox.showerror("Error", "Selected file is not a DDS image! It will not be imported!")
                f.close()
            else:
                inputSize = self.getFileSize(f)
                if inputSize > self.currentSize:
                    msgBox = messagebox.showerror("Error", "Selected DDS size is too large! It will not be imported!")
                    f.close()
                else:
                    f.seek(0x0C, os.SEEK_CUR)
                    height = struct.unpack('I', f.read(4))[0]
                    width = struct.unpack('I', f.read(4))[0]
                    f.seek(0x08, os.SEEK_CUR)
                    mips = struct.unpack('I', f.read(4))[0]
                    self.fb.seek(self.ddsEntry)
                    self.fb.write(struct.pack('I', height))
                    self.fb.write(struct.pack('I', width))
                    self.fb.write(struct.pack('I', mips))
                    f.seek(0x00, os.SEEK_SET)
                    inputTexture = f.read()
                    self.fb.seek(self.ddsLocation, os.SEEK_SET)
                    self.fb.write(inputTexture)
                    msgBox = messagebox.showinfo("Info", "Texture replaced successfully.")
                    f.close()
                    # Call load texture so the change is visible
                    self.loadTexture()
        except FileNotFoundError:
            pass

root = tk.Tk()
root.resizable(0, 0)
gui = nupEditor(root)
root.mainloop()
