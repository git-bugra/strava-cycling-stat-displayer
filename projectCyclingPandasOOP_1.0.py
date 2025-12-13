import pandas as pd
import sys
import pathlib as pl
import tkinter as tk
import matplotlib as mpl
from tkinter import filedialog
from tkinter.ttk import Treeview
from tkinter import ttk
from tkinter import messagebox as mbox

background_color_main='#262624'
text_color="#E9E9E9"
button_backg_color="#30302E"
module_level={}

class CycloMeter():
    def __init__(self, path):
        self.pathAssign(path)
        self.msToKM('average speed')
        self.msToKM('max speed')
        self.secsToHour('moving time')
        self.condition=None
        self.sort_column = None
        self.sort_ascending = True

    def pathAssign(self, path: str):
        path = pl.Path(path)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            raise IOError(f"Failed to read CSV: {e}") from e
        df.columns = [c.lower() for c in df.columns]
        self.data = df.copy()   # keep copy
        return self
    
    def sortValues(self, column):
        
        if self.sort_column==column:
            self.sort_ascending=not self.sort_ascending
        else:
            self.sort_ascending=True
        
        self.sort_column=column
        self.data = self.data.sort_values(by=column, ascending=self.sort_ascending)
        
    
    def setCondition(self, condition):
        if condition is None:
            self.condition=None
        else:
            self.condition=condition
    
    def filterResults(self, column: str, operator: str, value: float):
        if column=='':
            condition=None
            self.setCondition(condition)
            print('Filter is removed, insert table for default view.')
            pass
        elif operator == ">":
            value=int(value)
            condition=self.data[column]>value
            self.setCondition(condition)
            print('Filterization is complete!')
        elif operator == "<":
            value=int(value)
            condition=self.data[column]<value
            self.setCondition(condition)
            print('Filterization is complete!')
        else:
            print('Invalid operator. (< or >)')
            return False
    
    def extractColumn(self, column:str):
        '''return column
        mutates self.data obj'''
        column=column.lower()
        if column in self.data.columns:
            return self.data[f"{column}"]
        else:
            raise KeyError("Column not found.")

    def extractMultiColumns(self, column:list):
        """Takes list with items as column str"""

        return self.data[column]

    def msToKM(self, column:str):
        col = column.lower()
        if col not in self.data.columns:
            raise KeyError(col)
        self.data = self.data.assign(**{f"{col} kmh": (self.data[col].astype(float) * 3.6).round(2)})

    def secsToHour(self, column):
        '''convert speed format to kmh'''
        if column in self.data.columns:
            meter=self.extractColumn(column)
            meter=meter/3600
            meter=round(meter, 3)
            self.data[f"{column}/h"]=meter

class TextRedirector():
    def __init__(self, text_widget:tk.Text, delay=50):
        self.text_widget = text_widget
        self.delay = delay
        self.text = ""
        self.index = 0

    def write(self,text):
        if self.index == 0:
            self.text_widget.configure(state='normal')
            self.text_widget.delete("1.0", "end")
            self.text_widget.configure(state='disabled')
            self.text = text
            self.insert_next_char()

    def insert_next_char(self):
        if self.index < len(self.text):
            char = self.text[self.index]
            self.text_widget.configure(state='normal')
            self.text_widget.insert("end", char)
            self.text_widget.see("end")
            self.text_widget.configure(state='disabled')

            self.index += 1
            self.text_widget.after(self.delay, self.insert_next_char)
        else:
            self.index = 0

    def flush(self):
        pass

def loadFile():
    
    items=['activity id', 'activity date', 'moving time/h', 'distance', 'max heart rate', 'average heart rate', 'average speed kmh', 'max speed kmh', 'average watts', 'calories'] 
    
    path=filedialog.askopenfilename()
    if path:
        cyclingObj=CycloMeter(path)
        cyclingObj.data=cyclingObj.data[items]
        module_level['obj']=cyclingObj
    else:
        pass
    return cyclingObj

def displayData(cyclingObj:CycloMeter):
    
    if cyclingObj.condition is not None: #If data is filtered, adjust the view.
        display_data:pd.Dataframe=cyclingObj.data[cyclingObj.condition]
    else: #Unfiltered, raw data copy.
        display_data:pd.Dataframe=cyclingObj.data #iterate dataframe records and get Series
    return display_data

def updateStatusBar(status_bar:tk.Text):
    sys.stdout=TextRedirector(status_bar)
    

def treeview_init(tree_view:Treeview, display_data, pandasRows, cyclingObj:CycloMeter):
    '''Adjust, insert and clear treeview'''
    for t in tree_view.get_children(): tree_view.delete(t)
    for i in list(display_data.columns): 
        
        #A bit complex but briefly, when clicked calls on sortedValues then 
        # insertTable again, sortedValues directly mutates the self.data then 
        # insertedtable just normally calls on that object with mutated data etc
        tree_view.heading(i, text=i, command=lambda col=i: (cyclingObj.sortValues(col), insertTable(tree_view, cyclingObj))) 
        
        tree_view.column(i, width=180) #column sorting
    
    for index, value in pandasRows: #Iterating through pandasRows
        print(value, index)
        raw_values=value.values #Series obj (bool T/F) to raw values
        tree_view.insert('','end',values=raw_values.tolist()) #''(start) to end insertion of columns not records
    print(f"Table insertion is complete!") #debugging needs removed on scaffolding

def insertTable(tree_view, cyclingObj:CycloMeter):

    display_data=displayData(cyclingObj)
    tree_view['columns']=list(display_data.columns) #update tree_view obj
    tree_view.column('#0', width=0, stretch=False)
    pandasRows=display_data.iterrows() #iterate dataframe records and get Series
    treeview_init(tree_view, display_data, pandasRows, cyclingObj)

def retrieveEntry(colmn,op,setVal, cyclingObj:CycloMeter):
    '''Return input of textBox'''
    colmn=colmn.get()
    operator=op.get()
    val=setVal.get()
    cyclingObj.filterResults(colmn,operator,val)

def initButtons(window):
    for i in range(4):
        if i==0:
            frame_1=tk.Frame(window)
            colmn=tk.Entry(frame_1)
            
        elif i==1:
            frame_2=tk.Frame(window)
            op=tk.Entry(frame_2)
            
        elif i==2:
            frame_3=tk.Frame(window)
            setVal=tk.Entry(frame_3)
        elif i==3:
            frame_4=tk.Frame(window)
            
    return colmn,op,setVal,frame_1,frame_2,frame_3, frame_4

def packButtons(colmn,op,setVal,frame_1,frame_2,frame_3, frame_4):
    
    
    for index, value in enumerate(["Column:", "Operation:", "Set Value:"]):
        
        if index==0:
            colmLabel=tk.Label(frame_1, text='column:')
            frame_1.pack(side='top')
            colmn.pack(side=tk.RIGHT)
            colmLabel.pack(side=tk.LEFT)
            
        elif index==1:
            operatorLabel=tk.Label(frame_2, text='operator:')
            frame_2.pack(side='top')
            op.pack(side=tk.RIGHT)
            operatorLabel.pack(side=tk.LEFT)
            
        elif index==2:
            valueLabel=tk.Label(frame_3, text='value:')
            frame_3.pack(side='top')
            setVal.pack(side=tk.RIGHT)
            valueLabel.pack(side=tk.LEFT)

    status_bar=tk.Text(frame_4, state='disabled')
    frame_4.pack(side='right', fill="x")
    status_bar.pack(fill="x") 
    updateStatusBar(status_bar) 

def applyStyle(window:tk.Tk, style:ttk.Style):
    window.option_add('*Text.font', ('Segoe UI', 12))
    style.theme_use('clam')
    
    layers=['*Button', '*Text', '*Label', '*Entry']
    
    for i in layers: 
            window.option_add(f'{i}.foreground', text_color)
            window.option_add(f'{i}.background', button_backg_color)

#Dict styling applications. Clean, sweet, warm... :D
    background='#262624'
    foreground='#E9E9E9'
    fieldbackground='#262624'
    dictionary={
        'Treeview':
        {
            'foreground':foreground,
            'background':background,
            'fieldbackground':fieldbackground,
            'font':('Segoe UI', 12)
        },
        'Treeview.Heading':
        {
            'foreground':foreground,
            'background':background,
            'fieldbackground':fieldbackground
        }
    }
    
    for widget_names, properties in dictionary.items():
            style.configure(widget_names,**properties) #KWARGS is where magic happens, makes key value pairs form variable. e.g. background='#262624'

    background=('pressed', '!disabled', "#6791C1"), ('active', '#262624')
    foreground=('pressed', '#E9E9E9'), ('active', '#E9E9E9')
    dictionary={
        'Treeview': 
        {
            'foreground':foreground,
            'background':(('selected','#6793C1'),)+background
        },
        'Treeview.Heading':
        {
            'foreground':foreground,
            'background':background,
        }
    }

    for widget_name, properties in dictionary.items():
        style.map(widget_name,**properties)
    
def programInitialize():
    
    window=tk.Tk(className="cycloMeter")
    window.configure(background=background_color_main)
    window.geometry('1200x800')
    style=ttk.Style(master=window)
    applyStyle(window,style)

    tree_view=Treeview(window, height=26)
    buttonLoadFile=tk.Button(window, text='Load CSV File', command=loadFile)
    
    buttonInsertTable=tk.Button(window, text="Insert Table", command=lambda: insertTable(tree_view, module_level['obj']))
    colmn, op, setVal, frame_1, frame_2, frame_3, frame_4=initButtons(window)

    buttonFilter=tk.Button(window, text='Filter', command=lambda:retrieveEntry(colmn,op,setVal, module_level['obj'])) #text box
    
    
    for i in [tree_view,buttonLoadFile,buttonFilter,buttonInsertTable]: i.pack()
    packButtons(colmn,op,setVal,frame_1,frame_2,frame_3, frame_4)
    
    window.mainloop()

if __name__ == "__main__":
    programInitialize()
    
    """
    STATUS: 
        Loading columns, data works
        Filtering works
        Interface is a bit better
        .exe file is ready

    
    TODO:
        Imperative programming needs removal or improvement.
        Global variables left and right, try to remove and implement better iFace
        When clicked on column, sort it by highest.
        Filterization is single dimensional, increase it for multiple columns and filterizations
    
    """