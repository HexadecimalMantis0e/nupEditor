from Tkinter import *
import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox
from PIL import Image, ImageTk
import os
import struct
import io

class nupGui:
    def __init__(self, window):
        window.title("nupEditor")
        self.menuBar = tk.Menu(window)
        self.menuBar.add_command(label="Open Nup", command=lambda: self.nupOpen())
        self.menuBar.add_command(label="Save Nup", state = "disabled", command=lambda: self.nupSave())
        self.menuBar.add_command(label="Replace Texture", state = "disabled", command=lambda: self.replaceTexture())
        self.menuBar.add_command(label="Save Texture", state = "disabled", command=lambda: self.saveTexture())
        window.config(menu=self.menuBar)
        self.listLabel = Label(window, text = "Select texture: ")
        self.listLabel.grid(row = 0, column = 0)
        self.listNumber = tk.StringVar()
        self.listDropDown = ttk.Combobox(window, width = 4, textvariable = self.listNumber)
        self.listDropDown["values"]
        self.listDropDown.grid(row = 0, column = 1)
        self.listDropDown.bind("<<ComboboxSelected>>", self.loadTextureEvent)
        self.textureCanvas = tk.Canvas(window, bg="gray", highlightthickness=1, highlightbackground="#666666", height=522, width=522)
        self.textureCanvas.grid(row=1, column=2)

    def clearData(self):
        self.fb = io.BytesIO()
        self.listDropDown.set("")
        self.listDropDown["values"] = []
        self.textureCanvas.delete("all")
        self.menuBar.entryconfig("Save Nup", state = "disabled")
        self.menuBar.entryconfig("Replace Texture", state = "disabled")
        self.menuBar.entryconfig("Save Texture", state = "disabled")

    def nupOpen(self):
        name = tkFileDialog.askopenfilename(filetypes = (("Bionicle Heroes NU20", "*.nup"),("All Files","*.*")), title = "Choose a file.")
        f = open(name,"rb")
        magic = f.read(0x04)
        if magic != "NU20":
            MsgBox = tkMessageBox.showwarning("Warning", "Selected file is not a NUP archive! It will not be loaded!", icon = "warning")
            f.close()
            self.clearData()
        else:
            f.seek(0x00, os.SEEK_SET)
            fileBytes = f.read()
            f.close()
            self.fb = io.BytesIO(fileBytes)
            self.indexLocation = self.linearScan(self.fb)
            if self.indexLocation is None:
                MsgBox = tkMessageBox.showwarning("Warning", "Texture index not found in NUP archive!", icon = "warning")
                self.clearData()
            else:
                self.fb.seek(self.indexLocation, os.SEEK_SET)
                fullSize = struct.unpack('I', self.fb.read(4))[0]
                self.indexCount = struct.unpack('I', self.fb.read(4))[0]
                if self.indexCount == 0x00:
                    MsgBox = tkMessageBox.showwarning("Warning", "No textures in index!", icon = "warning")
                    self.clearData()
                else:
                    self.fb.seek(0x08, os.SEEK_CUR)
                    self.indexSize = struct.unpack('I', self.fb.read(4))[0]
                    self.fb.seek(0x08, os.SEEK_CUR)
                    self.imageList = []
                    imageListCount = []
                    for i in range(0, self.indexCount):
                        entryWidthTemp = struct.unpack('I', self.fb.read(4))[0]
                        entryHeightTemp = struct.unpack('I', self.fb.read(4))[0]
                        entryMipCountTemp = struct.unpack('I', self.fb.read(4))[0]
                        self.fb.seek(0x04, os.SEEK_CUR)
                        entryAddress = struct.unpack('I', self.fb.read(4))[0]
                        if ((entryWidthTemp != 0x00) and (entryHeightTemp != 0x00)):
                            self.imageList.append(entryAddress)
                        self.menuBar.entryconfig("Save Nup", state = "active")
                        self.menuBar.entryconfig("Replace Texture", state = "active")
                        self.menuBar.entryconfig("Save Texture", state = "active")
                    # Init the dropdown
                    for i in range(0, len(self.imageList)):
                        imageListCount.append(i+1)
                    self.listDropDown["values"] = imageListCount
                    self.listDropDown.current(0)
                    self.loadTexture()

    def linearScan(self, filePointer):
        sFlag = False
        theSize = self.getFileSize(filePointer)
        fileSizeDiv = theSize // 0x04
        for i in range(0,fileSizeDiv):
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

    def nupSave(self):
        saveNupName = tkFileDialog.asksaveasfile(mode='wb', defaultextension=".nup")
        self.fb.seek(0x00, os.SEEK_SET)
        fileBytes = self.fb.read()
        saveNupName.write(fileBytes)
        saveNupName.close()

    def saveTexture(self):
        saveTextureName = tkFileDialog.asksaveasfile(mode='wb', defaultextension=".dds")
        self.fb.seek(self.ddsLocation, os.SEEK_SET)
        fileBytes = self.fb.read(self.currentSize)
        saveTextureName.write(fileBytes)
        saveTextureName.close()

    def loadTexture(self):
        self.ddsLocation = self.imageList[int(self.listDropDown.get())-1] + self.indexLocation + self.indexSize + 0x04
        self.fb.seek(self.ddsLocation, os.SEEK_SET)
        self.fb.seek(0x0C, os.SEEK_CUR)
        ddsHeight = struct.unpack('I', self.fb.read(4))[0]
        ddsWidth = struct.unpack('I', self.fb.read(4))[0]
        self.fb.seek(0x08, os.SEEK_CUR)
        ddsMips = struct.unpack('I', self.fb.read(4))[0]
        self.fb.seek(-0x20, os.SEEK_CUR)
        if ddsMips == 0x00:
            self.currentSize = (ddsWidth * ddsHeight * 0x06 ) + 0x80
        else:
            self.currentSize = (ddsWidth * ddsHeight) + 0x80
        for i in range(0x01, ddsMips):
            ddsWidth //= 0x02
            ddsHeight //= 0x02
            self.currentSize += max(0x01, ((ddsWidth + 0x03) / 0x04)) * max(0x01, ((ddsHeight + 0x03) / 0x04)) * 0x10
        pal = self.fb.read(self.currentSize)
        f = io.BytesIO(pal)
        self.currentTexture = Image.open(f)
        self.currentTexture = ImageTk.PhotoImage(self.currentTexture)
        self.textureCanvas.create_image (int(self.textureCanvas.winfo_width())/2, int(self.textureCanvas.winfo_height())/2, image = self.currentTexture)

    def loadTextureEvent(self,event):
        self.loadTexture()

    def replaceTexture(self):
        name = tkFileDialog.askopenfilename(filetypes = (("DDS image", "*.dds"),("All Files","*.*")), title = "Choose a file.")
        f = open(name,"rb")
        magic = f.read(0x03)
        if magic != "DDS":
            MsgBox = tkMessageBox.showwarning("Warning", "Selected file is not a DDS image! It will not be imported!", icon = "warning")
            f.close()
        else:
            inputSize = self.getFileSize(f)
            if inputSize > self.currentSize:
                MsgBox = tkMessageBox.showwarning("Warning", "Selected DDS size is too large! It will not be imported!", icon = "warning")
                f.close()
            else:
                inputTexture = f.read()
                self.fb.seek(self.ddsLocation, os.SEEK_SET)
                self.fb.write(inputTexture)
                MsgBox = tkMessageBox.showinfo("Info", "Texture replaced successfully.")
                f.close()
                # Call load texture so the change is visible
                self.loadTexture()

root = tk.Tk()
root.resizable(0, 0)
gui = nupGui(root)
root.mainloop()
