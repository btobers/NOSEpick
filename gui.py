"""
NOSEpick - currently in development stages
created by: Brandon S. Tober and Michael S. Christoffersen
date: 25JUN19
last updated: 19SEP2019
environment requirements in nose_env.yml
"""

### IMPORTS ###
# import ingester
import imPick, wvPick, basemap, utils, ingester
import os, sys, scipy, glob
import numpy as np
import matplotlib as mpl
mpl.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import tkinter.ttk as ttk

# MainGUI is the NOSEpick class which sets the gui interface and holds operating variables
class MainGUI(tk.Frame):
    def __init__(self, parent, in_path, out_path, map_path, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.in_path = in_path
        self.out_path = out_path
        self.map_path = map_path
        self.setup()


    # setup is a method which generates the app menubar and buttons and initializes some vars
    def setup(self):
        self.f_loadName = ""
        self.f_saveName = ""
        self.map_loadName = "" 

        # generate menubar
        menubar = tk.Menu(self.parent)

        # create individual menubar items
        fileMenu = tk.Menu(menubar, tearoff=0)
        pickMenu = tk.Menu(menubar, tearoff=0)
        mapMenu = tk.Menu(menubar, tearoff=0)
        helpMenu = tk.Menu(menubar, tearoff=0)

        # file menu items
        fileMenu.add_command(label="Open    [Ctrl+O]", command=self.open_data)
        fileMenu.add_command(label="Save    [Ctrl+S]", command=self.save_loc)
        fileMenu.add_command(label="Next     [Right]", command=self.next_loc)
        fileMenu.add_command(label="Exit    [Ctrl+Q]", command=self.close_window)

        # pick menu items
        pickMenu.add_command(label="New     [Ctrl+N]", command=self.new_pick)
        pickMenu.add_command(label="Stop    [Escape]", command=self.stop_pick)
        pickMenu.add_separator()
        pickMenu.add_command(label="Optimize", command=self.pick_opt)

        # map menu items
        mapMenu.add_command(label="Open     [Ctrl+M]", command=self.map_loc)

        # help menu items
        helpMenu.add_command(label="Instructions", command=self.help)
        helpMenu.add_command(label="Keyboard Shortcuts", command=self.shortcuts)

        # add items to menubar
        menubar.add_cascade(label="File", menu=fileMenu)
        menubar.add_cascade(label="Pick", menu=pickMenu)
        menubar.add_cascade(label="Map", menu=mapMenu)
        menubar.add_cascade(label="Help", menu=helpMenu)
        
        # add the menubar to the window
        self.parent.config(menu=menubar)

        #configure imPick and wvPick tabs
        self.nb = ttk.Notebook(self.parent)
        self.nb.pack(side="top",anchor='w', fill="both", expand=1)
        self.imTab = tk.Frame(self.parent)
        self.imTab.pack()
        self.nb.add(self.imTab, text='imagePick')
        self.wvTab = tk.Frame(self.parent)
        self.wvTab.pack()
        self.nb.add(self.wvTab, text='wavePick')

        # bind tab change event to send pick data to wvPick if tab switched from imPick
        self.nb.bind("<<NotebookTabChanged>>", self.pick_opt)

        # initialize imPick
        self.imPick = imPick.imPick(self.imTab)
        self.imPick.set_vars()
        self.imPick.start_im()

        # initialize wvPick
        self.wvPick = wvPick.wvPick(self.wvTab)

        # bind keypress events
        self.parent.bind("<Key>", self.key)

        # handle x-button closing of window
        self.parent.protocol("WM_DELETE_WINDOW", self.close_window)

        self.open_data()


    # key is a method to handle UI keypress events
    def key(self,event):
        # event.state & 4 True for Ctrl+Key
        # event.state & 1 True for Shift+Key
        # Ctrl+O open file
        if event.state & 4 and event.keysym == "o":
            self.open_data()

        # Ctrl+S save picks
        elif event.state & 4 and event.keysym == "s":
            self.save_loc()

        # Ctrl+M open map
        elif event.state & 4 and event.keysym == "m":
            self.map_loc()

        # Ctrl+N begin pick
        elif event.state & 4 and event.keysym == "n":
            self.new_pick()

        # Ctrl+Q close NOSEpick
        elif event.state & 4 and event.keysym == "q":
            self.close_window()

        # shift+. (>) next file
        elif event.keysym =="Right":
            self.next_loc()

        # Escape key to stop picking current layer
        elif event.keysym == "Escape":
            self.stop_pick()

        # c key to clear all picks in imPick
        if event.keysym =="c":
            # clear the drawing of line segments
            self.imPick.clear_picks()

        # BackSpace to clear last pick 
        elif event.keysym =="BackSpace":
            self.imPick.clear_last()

        # Delete key to remove most recent pick layer
        elif event.keysym =="Delete":
            self.imPick.delete_pkLayer()

        # Space key to toggle imPick between radar image and clutter
        elif event.keysym=="space":
            self.imPick.set_im()


    # close_window is a gui method to exit NOSEpick
    def close_window(self):
        # check if picks have been made and saved
        if self.imPick.get_pickLen() > 0 and self.f_saveName == "":
            if tk.messagebox.askokcancel("Warning", "Exit NOSEpick without saving picks?", icon = "warning") == True:
                self.parent.destroy()
        else:
            self.parent.destroy()


    # open_data is a gui method which has the user select and input data file - then passed to imPick.load()
    def open_data(self):
        temp_loadName = ""
        # select input file
        # temp_loadName = tk.filedialog.askopenfilename(initialdir = self.in_path,title = "Select file",filetypes = (("hd5f files", ".mat .h5"),("segy files", ".sgy"),("all files",".*")))
        temp_loadName = "/mnt/Swaps/MARS/targ/supl/UAF/2018/aug/export/20180817-222930.mat"
        # if input selected, clear imPick canvas, ingest data and pass to imPick
        if temp_loadName:
            self.f_loadName = temp_loadName
            self.imPick.clear_canvas()  
            self.imPick.set_vars()
            # ingest the data
            self.igst = ingester.ingester(self.f_loadName.split(".")[-1])
            self.data = self.igst.read(self.f_loadName)
            self.imPick.load(self.f_loadName, self.data)
            self.wvPick.set_data(self.data["amp"], self.data["dt"], self.data["num_sample"])

        # pass basemap to imPick for plotting pick location
        if self.map_loadName:
            self.basemap.clear_nav()
            self.basemap.set_nav(self.imPick.get_nav(), self.f_loadName)
            self.imPick.get_basemap(self.basemap)            


    # save_loc is method to receieve the desired pick save location from user input
    def save_loc(self):
        if self.f_loadName and self.imPick.get_pickLen() > 0:
            self.f_saveName = tk.filedialog.asksaveasfilename(initialfile = os.path.splitext(self.f_loadName.split("/")[-1])[0] + "_pk",
                                initialdir = self.out_path,title = "Save As",filetypes = (("comma-separated values","*.csv"),))
        if self.f_saveName:
            self.stop_pick()
            self.imPick.save(self.f_saveName)
    

    # map_loc is a method to get the desired basemap location and initialize
    def map_loc(self):
        self.map_loadName = tk.filedialog.askopenfilename(initialdir = self.map_path, title = "Select file", filetypes = (("GeoTIFF files","*.tif"),("all files","*.*")))
            
        if self.map_loadName:
            self.basemap = basemap.basemap(self.parent, self.map_loadName)
            self.basemap.map()

            if self.f_loadName:
                # pass basemap to imPick for plotting pick location
                self.basemap.set_nav(self.imPick.get_nav(), self.f_loadName)
                self.imPick.get_basemap(self.basemap)


    # new_pick is a method which begins a new imPick pick layer
    def new_pick(self):
        if self.f_loadName:
            self.imPick.set_pickState(True)
            self.imPick.plot_picks()
            self.imPick.blit()


    # stop_pick is a method which terminates the current imPick pick layer
    def stop_pick(self):
        if self.imPick.get_pickState() is True:
            self.imPick.set_pickState(False)
            self.imPick.plot_picks()
            self.imPick.blit()


    # next_loc is a method to get the filename of the next data file in the directory then call imPick.load()
    def next_loc(self):
        if self.f_loadName and self.imPick.nextSave_warning() == True:
            # get index of crurrently displayed file in directory
            file_path = self.f_loadName.rstrip(self.f_loadName.split("/")[-1])
            file_list = []

            # step through files in current directory of same extension as currently loaded data
            # determine index of currently loaded data within directory 
            for count,file in enumerate(sorted(glob.glob(file_path + "*." + self.f_loadName.split(".")[-1]))):
                file_list.append(file)
                if file == self.f_loadName:
                    file_index = count

            # add one to index to load next file
            file_index += 1

            # check if more files exist in directory following current file
            if file_index <= (len(file_list) - 1):
                self.f_loadName = file_list[file_index]
                self.imPick.clear_canvas()
                self.imPick.set_vars()
                self.data = self.igst.read(self.f_loadName)
                self.imPick.load(self.f_loadName, self.data)


                if self.map_loadName and self.basemap.get_state() == 1:
                    self.basemap.clear_nav()
                    self.basemap.set_nav(self.imPick.get_nav(), self.f_loadName)
                    self.imPick.get_basemap(self.basemap)

            else:
                print("Note: " + self.f_loadName.split("/")[-1] + " is the last file in " + file_path + "*." + self.f_loadName.split(".")[-1])
    
    # pick_opt is a method to load the wvPick optimization tools
    def pick_opt(self, event):
        selection = event.widget.select()
        tab = event.widget.tab(selection, "text")
        # first determine if at least one picking layer exists
        if (tab == "wavePick") and (self.imPick.get_numPkLyrs() > 0):
            # set picking state to false
            self.imPick.set_pickState(False)
            self.imPick.plot_picks()
            self.imPick.blit()
            # get pick layer from imPick and pass to wvPick
            self.wvPick.set_pickDict(self.imPick.get_pickDict())
            self.wvPick.plot_wv()


    def help(self):
        # help message box
        tk.messagebox.showinfo("Instructions",
        """Nearly Optimal Subsurface Extractor:
        \n\n1. File->Load to load data file
        \n2. Map->Open to load basemap
        \n3. Pick->New to begin new pick layer 
        \n4. Click along reflector surface to pick\n   horizon
        \n\t\u2022[backspace] to remove the last
        \n\t\u2022[c] to remove all
        \n5. Pick->Stop to end current pick layer
        \n6. Radio buttons to toggle between radar\n   and clutter images
        \n7. File->Save to export picks
        \n8. File->Next to load next data file
        \n9. File->Quit to exit application""")


    def shortcuts(self):
        # shortcut list
        tk.messagebox.showinfo("Keyboard Shortcuts",
        """General:
        \n[Ctrl+o]\tOpen radar data file
        \n[Ctrl+m]\tOpen basemap window
        \n[Ctrl+n]\tBegin new pick layer
        \n[Escape]\tEnd current pick layer
        \n[Spacebar]\tToggle between radar and clutter images
        \n[Ctrl+s]\tExport pick data
        \n[Right]\t\tOpen next file in directory
        \n[Ctrl+q]\tQuit NOSEpick
        \n\nPicking:
        \n[Backspace]\tRemove last pick event
        \n[Delete]\tRemove current/ most recent pick layer
        \n[c]\t\tRemove all picked layers""")