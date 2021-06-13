import tkinter
import requests
from tkinter import Label, LabelFrame, Toplevel, ttk
from Blind import Time_Based_SQL_Injection as timeBasedInjection
from Blind import Blind_SQL_Injection as booleanInjection
#from Error import Error_Based_SQL as errorBasedInjection
from Query import Union_Query_Based_SQL_Injection as queryBasedInjection
#from Stacked_Query import Stacked_Query_SQL as stckedQueryInjection


# url = 'https://webhacking.kr/challenge/bonus-1/index.php'
# url = 'http://104.197.42.200/member/login_ok.php'
cookies = {'PHPSESSID': 'd42rp6qqm5fhj3dmn3830g74pq'}


class Injection(Toplevel):
    def __init__(self, parent, type):
        super().__init__(parent)
        self.parent = parent
        self.title(type+" Based Injection Tools")
        self.geometry("480x400+100+100")
        self.resizable(False, False)
        # Label Frame Settings
        self.labelframe = tkinter.LabelFrame(self, padx=100, pady=5)
        self.labelframe.place(x=30, y=110)
        self.dbList = []
        self.tableList = []
        self.columnList = []
        if type == "Time":
            self.getDBbtn = tkinter.Button(self, text="Get Databases", command=lambda: [timeBasedInjection.find_db_name(self.dbList, self.urlTbox.get(),cookies), self.refresh()], width=11, height=1)
            self.getTBbtn = tkinter.Button(self, text="Get Tables", command=lambda: [timeBasedInjection.find_table_name(self.tableList, self.urlTbox.get(), cookies, self.dbComboBox.get()), self.refresh()], width=11)
            self.getCMbtn = tkinter.Button(self, text="Get Columns", command=lambda: [timeBasedInjection.find_column_name(self.columnList, self.urlTbox.get(), cookies, self.tableComboBox.get()), self.refresh()], width=11)
            self.getDPbtn = tkinter.Button(self, text="Dump", command=lambda: [timeBasedInjection.dump_data(self.urlTbox.get(),cookies, self.tableComboBox.get(), self.columnList), self.refresh()], width=11)
        elif type == "Blind":
            self.getDBbtn = tkinter.Button(self, text="Get Databases", command=lambda: [booleanInjection.find_db_name(self.dbList, self.urlTbox.get(),cookies), self.refresh()], width=11, height=1)
            self.getTBbtn = tkinter.Button(self, text="Get Tables", command=lambda: [booleanInjection.find_table_name(self.tableList, self.urlTbox.get(), cookies, self.dbComboBox.get()), self.refresh()], width=11)
            self.getCMbtn = tkinter.Button(self, text="Get Columns", command=lambda: [booleanInjection.find_column_name(self.columnList, self.urlTbox.get(), cookies, self.tableComboBox.get()), self.refresh()], width=11)
            self.getDPbtn = tkinter.Button(self, text="Dump", command=lambda: [booleanInjection.dump_data(self.urlTbox.get(),cookies, self.tableComboBox.get(), self.columnList), self.refresh()], width=11)
        elif type == "Union Query":
            self.getDBbtn = tkinter.Button(self, text="Get Databases", command=lambda: [queryBasedInjection.find_db_name(self.dbList, self.urlTbox.get(),cookies), self.refresh()], width=11, height=1)
            self.getTBbtn = tkinter.Button(self, text="Get Tables", command=lambda: [queryBasedInjection.find_table_name(self.tableList, self.urlTbox.get(), cookies, self.dbComboBox.get()), self.refresh()], width=11)
            self.getCMbtn = tkinter.Button(self, text="Get Columns", command=lambda: [queryBasedInjection.find_column_name(self.columnList, self.urlTbox.get(), cookies, self.dbComboBox.get(), self.tableComboBox.get()), self.refresh()], width=11)
            self.getDPbtn = tkinter.Button(self, text="Dump", command=lambda: [queryBasedInjection.dump_data(self.urlTbox.get(),cookies, self.dbComboBox.get(), self.tableComboBox.get(), self.columnList), self.refresh()], width=11)

        # else:

        self.showdbBtn = tkinter.Button(self, text= "show", command=self.show, width=10)
        self.showdbBtn.place(x=30, y=50)
        self.getDBbtn.place(x=360, y=228)
        self.urlLabel = tkinter.Label(self, text="URL")
        self.urlLabel.place(x=30, y=230)

        self.urlTbox = tkinter.Entry(self, width=40)
        self.urlTbox.place(x=70, y=230)
        #
        # Get Tables Button
#        self.getTBbtn = tkinter.Button(self, text="Get Tables", command=getDatabase, width=11)
        self.getTBbtn.place(x=360, y=258)

        self.dbLabel = tkinter.Label(self, text="Database")
        self.dbLabel.place(x=30, y=260)

        
        self.dbComboBox = tkinter.ttk.Combobox(self, height=15, values= self.dbList)
        self.dbComboBox.place(x=90, y=260)
        # Get Columns Button
#        self.getCMbtn = tkinter.Button(self, text="Get Columns", command=getDatabase, width=11)
        self.getCMbtn.place(x=360, y=288)

        self.tableLabel = tkinter.Label(self, text="Table Name")
        self.tableLabel.place(x=30, y=290)

        self.tableComboBox = tkinter.ttk.Combobox(self, height=15, values= self.tableList)
        self.tableComboBox.place(x=110, y=290)

        # Get Dump Button
#        self.getDPbtn = tkinter.Button(self, text="Dump", command=getDatabase, width=11)
        self.getDPbtn.place(x=360, y=318)

        self.columnLabel = tkinter.Label(self, text="Column's Name")
        self.columnLabel.place(x=30, y=320)

#        self.columnTbox = tkinter.Entry(self, width=31, state="disabled")
        self.columnComboBox = tkinter.ttk.Combobox(self, height=15, values= self.columnList)
        self.columnComboBox.place(x=130, y=320)
        self.mainloop()
    
    def show(self):
        print(self.values)

    def refresh(self):
        self.dbComboBox['values'] = self.dbList
        self.tableComboBox['values'] = self.tableList
        self.columnComboBox['values'] = self.columnList
        

mainWindow = tkinter.Tk()
mainWindow.title("SQL Injection Tools")
mainWindow.resizable(False, False)

blindInjectionBtn = tkinter.Button(mainWindow, text="Blind SQL Injection", command=lambda: Injection(mainWindow, "Blind"))
blindInjectionBtn.grid(row=0, column=0)
errorInjectionBtn = tkinter.Button(mainWindow, text="Error Based SQL Injection", command=lambda: Injection(mainWindow, "Error"))
errorInjectionBtn.grid(row=0, column=1)
timeInjectionBtn = tkinter.Button(mainWindow, text="Time Based SQL Injection", command=lambda: Injection(mainWindow, "Time"))
timeInjectionBtn.grid(row=1, column=0)
stackedInjectionBtn = tkinter.Button(mainWindow, text="Query Based SQL Injection", command=lambda: Injection(mainWindow, "Union Query"))
stackedInjectionBtn.grid(row=1, column=1)

mainWindow.mainloop()