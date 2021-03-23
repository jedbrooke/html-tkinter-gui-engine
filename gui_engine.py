"""
gui_engine.py
Written by Jasper Edbrooke
gui_engine.py contains the Form, Window, TagUtility, Button, and Field classes.
"""

from bs4 import BeautifulSoup as bs
import tkinter as tk
from tkinter import Canvas
from tkinter import messagebox as tkmb
from PIL import ImageTk,Image
import os
from io import BytesIO



class TagUtility():
    """TagUtility is a static class that hold some helper and utility functions that aid the Window class in parsing the HTML and beautiful soup data"""

    """Possible Arguments for grid function"""
    GRID_ARGS = {
        "padx":int,
        "pady":int,
        "sticky":str,
        "row":int,
        "column":int,
    }

    """Possible Arguments for listbox tag"""
    LISTBOX_ARGS = {
        "height":int,
        "width":int,
        "selectmode":str,
    }

    """Possible Arguments for button tag"""
    BUTTON_ARGS = {
        "link":str,
        "action":str,
        "btype":str,
        "title":str,
        "args":str,
    }

    """Possible Arguments for div (tk.frame) tag"""
    FRAME_ARGS = {
        "height":int,
        "width":int,
    }

    """Dictionary of tag names and their argument lists"""
    ELEMENT_ARGS = {
        "grid":GRID_ARGS,
        "listbox":LISTBOX_ARGS,
        "button":BUTTON_ARGS,
        "frame":FRAME_ARGS,
    }

    """gets the HTML from a file and returns a Beautiful Soup obejct for parsing"""
    @staticmethod
    def get_html(path):
        file = open(path)
        soup = bs(file,"lxml")
        return soup

    """casting function to cast "true" and "false" to bools"""
    @staticmethod
    def bool_from_str(s):
        return s.lower() == "true"

    """gets the requested attribute, if it exists, from the given bsoup tag"""
    @staticmethod
    def get_attribute(tag,attr,cast=str):
        try:
            return cast(tag[attr])
        except KeyError as e:
            return None
        except ValueError as e:
            return None

    """returns all the relevant arguments for a given tag and type"""
    @staticmethod
    def get_element_args(tag,element):
        return dict(\
            [(arg,TagUtility.get_attribute(tag,arg,kind))\
            for arg,kind in TagUtility.ELEMENT_ARGS[element].items()\
            if TagUtility.get_attribute(tag,arg,kind) is not None])

    """returns all the tags related to the grid arguments"""
    @staticmethod
    def get_grid_args(tag):
        return TagUtility.get_element_args(tag,"grid")

    """returns all the tags related to the listbox tag"""
    @staticmethod
    def get_listbox_args(tag):
        return TagUtility.get_element_args(tag,"listbox")

    """returns all the tags related to the button tag"""
    @staticmethod
    def get_button_args(tag):
        return TagUtility.get_element_args(tag,"button")

    """returns all the tags related to the div (tk.frame) tag"""
    @staticmethod
    def get_frame_args(tag):
        return TagUtility.get_element_args(tag,"frame")

    """returns an image in a format that tkinter can use"""
    """not really related to tags, but still a utility function"""
    @staticmethod
    def get_image(src,target_size=250,mode='path'):
        if mode == "path": 
            img_pil = Image.open(src)
        elif mode == 'blob':
            img_pil = Image.open(BytesIO(src))
        width,height = img_pil.size
        ratio = width/height
        width_new = target_size
        height_new = target_size/ratio
        img_pil = img_pil.resize((int(width_new), int(height_new)), Image.ANTIALIAS)
        return ImageTk.PhotoImage(img_pil)

class Button():
    """Button Base class, holds attribute for the button such as type and link and parent"""
    """Other windows will have their own derived versions of Button to hold the callback functions they will need"""
    def __init__(self, link=None, action=None, btype=None, title=None, window=None,args=None):
        self.link = link
        self.action = action
        self.btype = btype
        self.title = title
        self.window = window
        self.args = args
        if link and not btype:
            self.btype = "link"
        elif action and not btype:
            self.btype = "action"

class Form():
    """Form Base Class, holds the attributes and fields for the forms"""
    """Other windows will have their own derived version of the Form class to take the correct actions when the form is submitted"""
    def __init__(self,action=None,window=None):
        self.fields = {}
        self.window = window

    def add_field(self,field):
        """adds a field to the form"""
        self.fields[field.name] = field
        if field.ftype == "for_label":
            var = [f for f in self.fields if f.name == field.data[0]][0]
            field.data[1]["textvariable"] = var.data

    def add_to_multiple_select(self,field_name,data):
        sel = self.get_field(field_name)
        sel.data.append(data)

    def get_field(self,name):
        return self.fields[name]

    def print_all_fields(self):
        print(*self.fields)

    def submit(self):
        self.print_all_fields()

class Field():
    def __init__(self, ftype, name, data):
        self.ftype = ftype
        self.name = name
        self.data = data
    def __str__(self):
        return str([self.ftype,self.name,self.data])

class Window():
    """Window Base class, handles the psarsing of HTML text into tkinter widgets"""
    """Subclasses of Window will implement their own post() method, which handles some extra initializing of the window and input from forms"""
    client = None
    def __init__(self,soup=None,path=None,main=False,master=None,form=None,button=None,windows=None):
        """the functions to call for each tag type"""
        self.HEAD_ACTIONS = {
            "title":self.set_title,
            "geometry":self.set_geometry
        }
        
        """the functions to call for each tag type"""
        self.BODY_ACTIONS = {
            "button":self.create_button,
            "label":self.create_label,
            "div":self.create_frame,
            "scrollbox":lambda *args, **kwargs: self.create_listbox(scrolling=True,*args,**kwargs),
            "listbox":self.create_listbox,
            "img":self.create_image,
            "form":self.create_form,
            "input":self.create_input,
            "select":self.create_select,
            "option":self.create_option,
        }

        """Dictionary for buttons"""
        self.buttons = {}
        """If a button class type was passed use that, if not then use the defualt Button"""
        self.button = button if button else Button
        """List for images, PIL Tkimages will get garbage collected if the last reference goes out of scope so we will keep them here"""
        self.images = []
        """If a button form type was passed use that, if not then use the defualt Form"""
        self.form_type = form if form else Form
        """Dictionary for the forms and lists so we can add items to them later"""
        self.frames = {}
        """Types of windows for linked windows"""
        self.windows = windows
        self.isMain = main
        """Master is the tk.Tk or tk.Toplevel object that this window is a child to"""
        self.master = master
 
        """self.win is the toplevel tkinter widget for all the widgets in the window"""
        if main:
            self.win = tk.Tk()
            self.win.protocol("WM_DELETE_WINDOW", self.shut_down)
        else:
            self.win = tk.Toplevel()
            self.win.transient(master=master)
            self.win.grab_set()
            self.win.focus_set()

        """have one main frame for all the tkinter widgets to sit in"""
        self.main_frame = tk.Frame(self.win)

        if soup is None and path is not None:
            #if we were given a path and not a soup, get the soup from the file at the path
            self._initPath(path)
        elif soup is not None and path is None:
            # if we were givel the soup and not a path then we are good to go
            self.soup = soup

        """If this is the main window, we will initialize it now, otherwise the window will get intialized in its post() method"""
        if main:
            self._initialize()

    def start(self):
        """starts the mainloop"""
        self.win.mainloop()

    def _initialize(self):
        """This is where we actually start the process of converting all the HTML tags in the soup to tkinter widgets"""

        """instantiate a new form for the window"""
        self.form = self.form_type(window=self)
        """Buitld the elements"""
        self.buildElements()
        """grid the main frame so we can see all the widgets"""
        self.main_frame.grid()

    def _initPath(self,path):
        # get the soup from the file at the path
        self.soup = TagUtility.get_html(path)

    def shut_down(self):
        """handle the closing of the GUI"""
        self.win.quit()

    def post(self):
        # Default post behavior is to initialize all the elements, this is most likely overridden in derived classes
        self._initialize()   

    def buildElements(self):
        self.buildHead(self.soup.head)
        self.buildBody(self.soup.body,self.main_frame)

    def buildHead(self,soup):
        """Build the header elements, or metadata"""
        for tag in soup:
            if tag.name is not None:
                self.HEAD_ACTIONS[tag.name](tag)

    def buildBody(self,data,container,*args,**kwargs):
        """build the body elements, or the stuff we actially see"""
        elements = []
        for tag in data:
            if tag.name is not None:
                elements.append(self.BODY_ACTIONS[tag.name](tag,container,*args,**kwargs))
        return elements

    def buildList(self,elements,listbox):
        """accepts the elements for a listbox, and the listbox to add them to, and adds them"""
        l = [item.text for item in elements.find_all("li")]
        listbox.insert(tk.END,*l)
        return l


    def set_title(self,title):
        self.win.title(title.text)

    def set_geometry(self,geometry):
        self.win.geometry(geometry.text)

    def create_label(self,label,parent):
        """Creates a tk.Label from the html soup"""
        l = tk.Label(parent,text=label.text.strip())
        l.grid(TagUtility.get_grid_args(label))
        if TagUtility.get_attribute(label,"for"):
            name = TagUtility.get_attribute(label,"name")
            label_for = TagUtility.get_attribute(label,"for")
            self.form.add_field(Field("for_label",name,[label_for,l]))
        ltype = TagUtility.get_attribute(label,"type")
        if ltype and ltype == "display":
            name = TagUtility.get_attribute(label,"name")
            tksv =  tk.StringVar()
            l["textvariable"] = tksv
            self.form.add_field(Field("label",name,tksv))
        return l

    def create_button(self,button,parent):
        """Creates a tk.Button from the html soup"""
        if len(button.find_all("img")) != 0:
            icon = TagUtility.get_image(src=button.find_all("img")[0]["src"],target_size=20)
            b = tk.Button(parent,image=icon,text=button.text.strip(),height=20,width=20)
            self.images.append(icon)
        else: 
            b = tk.Button(parent,text=button.text.strip())
        b.grid(TagUtility.get_grid_args(button))
        self.buttons[str(b)] = self.button(**TagUtility.get_button_args(button),window=self)
        b.bind("<Button-1>",self.button_clicked)
        return b

    def create_frame(self,frame,parent,*args,**kwargs):
        """Creates a tk.Frame from the html soup, and fill it with widgets"""
        if TagUtility.get_attribute(frame,"scrolling",TagUtility.bool_from_str):
            return self.create_scrollframe(frame,parent,*args,**kwargs)
        else:
            tk_frame = tk.Frame(parent)
            elements = self.buildBody(frame,tk_frame,*args,**kwargs)
            tk_frame.grid(TagUtility.get_grid_args(frame))
            frame_id = TagUtility.get_attribute(frame,"id")
            if not frame_id:
                """if and ID isn't set, get it from the string cast of the tkinter widget"""
                frame_id = str(tk_frame)
            self.frames[frame_id] = tk_frame
            return (tk_frame,elements)


    def create_form(self,form,parent):
        """create a tk.frame for the Form object, and fill it with widgets"""
        form_frame = tk.Frame(parent)
        elements = self.buildBody(form,form_frame)
        form_frame.grid(TagUtility.get_grid_args(form))
        frame_id = TagUtility.get_attribute(form,"id")
        if not frame_id:
            """if and ID isn't set, get it from the string cast of the tkinter widget"""
            frame_id = str(form_frame)
        self.frames[frame_id] = form_frame
        return (form_frame,elements)


    def create_listbox(self,listbox,parent,scrolling=False):
        """Creates a tk.Listbox from the html soup"""
        if TagUtility.get_attribute(listbox,"scrolling",TagUtility.bool_from_str)\
         or scrolling:
            frame = tk.Frame(parent)
            parent = frame
            scrolling = True

        tk_listbox = tk.Listbox(parent,**TagUtility.get_listbox_args(listbox))
        list_items = self.buildList(listbox,tk_listbox)

        list_id = TagUtility.get_attribute(listbox,"id")
        if not list_id:
            """if and ID isn't set, get it from the string cast of the tkinter widget"""
            list_id = str(tk_listbox)
        self.frames[list_id] = tk_listbox

        if self.form:
            name = TagUtility.get_attribute(listbox,"name")
            self.form.add_field(Field("listbox",name,[tk_listbox,list_items]))

        if scrolling:
            scrollbar = tk.Scrollbar(frame,orient=tk.VERTICAL)
            scrollbar.grid(row=0,column=1,sticky=tk.N+tk.S)
            tk_listbox['yscrollcommand'] = scrollbar.set
            tk_listbox.grid(row=0,column=0,sticky=tk.N+tk.S+tk.E+tk.W)
            scrollbar['command'] = tk_listbox.yview
            frame.grid(TagUtility.get_grid_args(listbox))
            return frame
        else :
            tk_listbox.grid(TagUtility.get_grid_args(listbox))
            return tk_listbox

            
    def create_scrollframe(self,scrollframe,parent,*args,**kwargs):
        """Creates a tk.Frame from the html soup with a scrollbar, and fill it with widgets"""
        outer_frame = tk.Frame(parent,relief=tk.GROOVE,bd=1)
        outer_frame.grid(TagUtility.get_grid_args(scrollframe))

        canvas = tk.Canvas(outer_frame,highlightthickness=0)
        inner_frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(outer_frame,orient=tk.VERTICAL,command=canvas.yview)
        canvas['yscrollcommand']=scrollbar.set

        scrollbar.grid(row=0,column=1,sticky=tk.N+tk.S)
        canvas.grid(row=0,column=0,sticky=tk.W)
        canvas.create_window((0,0),window=inner_frame,anchor='nw')


        canvas.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all"),**TagUtility.get_frame_args(scrollframe)))

        frame_id = TagUtility.get_attribute(scrollframe,"id")
        if not frame_id:
            frame_id = str(inner_frame)
        self.frames[frame_id] = inner_frame
        outer_frame_id = "outer-"+frame_id
        self.frames[outer_frame_id] = outer_frame
        canvas_id = frame_id+"-canvas"
        self.frames[canvas_id] = canvas

        return (outer_frame,self.buildBody(scrollframe,inner_frame,*args,**kwargs))

    def create_image(self,tag,parent):
        """Creates an image from the html soup"""
        src = TagUtility.get_attribute(tag,"src")
        canvas = tk.Canvas(parent)
        canvas.grid()
        img = TagUtility.get_image(src,250)
        canvas.create_image(0,0,anchor=tk.N+tk.W, image=img)
        self.images.append(img)
        return canvas

    def button_clicked(self,event):
        """callback function for when buttons are clicked"""
        button = self.buttons[str(event.widget)]
        """call function corresponding to button type"""
        BUTTON_TYPE_ACTIONS[button.btype](self,button)
        

    def back_button(self,button):
        """Button for going back one window in the UI, closes the current window and puts focus on the previous one"""
        self.master.grab_set()
        self.master.focus_set()
        self.win.destroy()

    def link_clicked(self,button):
        if button.args:
            self.goto_link(button.link,button.args)
        else:
            self.goto_link(button.link)

    def goto_link(self,link,*args,**kwargs):
        """Sends the gui to the next window as denoted by the file in the path for the link"""
        path = os.path.join("gui_pages",f"{link}")
        print("link clicked:",link)
        if os.path.isfile(path):
            try:
                window = self.windows[link]
            except Exception as e:
                window = Window
            w = window(TagUtility.get_html(path),master=self.win)
            w.post(*args,**kwargs)

        else :
            tkmb.showerror(title="Page not Found", message=f"Error: \"{path}\" does not exist!")

    def button_action(self,button):
        """if the button is an action type try to execute the function in the Button class"""

        try:
            if button.args:
                getattr(button,button.action)(button.args)
            else:
                getattr(button,button.action)()
        except Exception as e:
            print(e)

    def create_input(self,input_tag,parent):
        """Creates an input for a form"""
        return INPUT_TYPE_ACTIONS[TagUtility.get_attribute(input_tag,"type")](self,input_tag,parent)

    def create_text_input(self,input_tag,parent):
        """creates a text input with the necessary tkinter widgets and back end in the Form class"""
        var = tk.StringVar()
        default = TagUtility.get_attribute(input_tag,"default")
        if default:
            var.set(default)
        entry = tk.Entry(parent,textvariable=var)
        entry.grid(TagUtility.get_grid_args(input_tag))
        self.form.add_field(Field(str,TagUtility.get_attribute(input_tag,"name"),var))
        return entry

    def create_submit_input(self,input_tag,parent):
        """creates the submit button for Forms"""
        text = TagUtility.get_attribute(input_tag,"text",str)
        button = tk.Button(parent, command=lambda : self.form.submit(), text=text)
        button.grid(TagUtility.get_grid_args(input_tag))
        return button

    def create_select(self,select,parent):
        """Creates a radio button or checkbutton set, creates tkinter widgets and Form items"""
        multiple = TagUtility.get_attribute(select,"multiple",TagUtility.bool_from_str)
        name = TagUtility.get_attribute(select,"name")
        if multiple:
            self.form.add_field(Field("multiple_select",name,[]))
            self.create_frame(select,parent,multiple=True,name=name)
        else:
            tksv = tk.StringVar()
            tksv.set(select.find_all("option")[0]['value'])
            self.form.add_field(Field("select",name,tksv))
            self.create_frame(select,parent,variable=tksv,multiple=False)

    def create_option(self,option,parent,variable=None,multiple=False,name=None):
        """Creates an option for the radio or check buttons"""
        value = TagUtility.get_attribute(option,"value")
        text = option.text.strip()
        if not value:
            value = text
        if multiple:
            tkiv = tk.IntVar()
            self.form.add_to_multiple_select(name,(tkiv,value))
            b = tk.Checkbutton(parent,text=text,variable=tkiv)

        else:
            b = tk.Radiobutton(parent,text=text,variable=variable,value=value)

        b.grid(TagUtility.get_grid_args(option))

        if len(option.find_all()) is 0:
            return b
        else :
            return (b,self.buildBody(option,parent))

    def get_frame_by_id(self,_id):
        """returns a reference to a frame based on the string ID"""
        return self.frames[_id]

    def post(self):
        """The initialize function, to be overwritten in Base classes, but provides a default behavior of initializing the window"""
        self._initialize()

    @staticmethod
    def set_client(_client):
        """Sets a static reference to the Client obejct so all Windows can interact with the client"""
        Window.client = _client
       
BUTTON_TYPE_ACTIONS = {
    "back":Window.back_button,
    "link":Window.link_clicked,
    "action":Window.button_action,
}

INPUT_TYPE_ACTIONS = {
    "text":Window.create_text_input,
    "submit":Window.create_submit_input,
}