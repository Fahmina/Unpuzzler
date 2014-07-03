#!/usr/bin/python
# -*- coding: utf-8 -*-

# newclass.py

# TODO: Check this automatically.
IS_WINDOWS = False

import os
import subprocess
import sys
import shutil
from datetime import datetime
import wx
from wx.lib.intctrl import IntCtrl
from wx import SpinCtrl
from wx.lib.agw.floatspin import FloatSpin
#if IS_WINDOWS:
#    from win32con import CREATE_NO_WINDOW 
from threading import Thread

global unpuzzle_script_file
global blender_directory
if IS_WINDOWS:
    blender_directory = "C:\\Program Files\\Blender Foundation\\Blender\\"
    firefox_path = "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
else:
    blender_directory = "/Applications/blender.app/Contents/MacOS/"


# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data        
        
# Thread class that executes processing
class Unpuzzle_Thread(Thread):
    """Worker Thread Class."""
    def __init__(self,notify_window,unpuzzle_path,unpuzzle_script_file,l_env):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
         
        self.unp_p = unpuzzle_path
        self.unp_scp = unpuzzle_script_file
        self.unp_env = l_env
        self._want_abort = 0
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
 
    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        # a long process (well, 10s here) as a simple loop - you will
        # need to structure your processing so that you periodically
        # peek at the abort variable
         

        if IS_WINDOWS:
            subprocess.call(blender_directory + "blender --python \"" + self.unp_scp + "\"",
                            env=self.unp_env)
                            #, creationflags=CREATE_NO_WINDOW)
        else:
            print("running: ")
            print(blender_directory + "blender --python "+self.unp_scp)
            subprocess.call([blender_directory + "blender",  "--python", self.unp_scp],
                            env=self.unp_env)
        
        # Here's where the result would be returned (this is an
        # example fixed result of the number 10, but it could be
        # any Python object)
        wx.PostEvent(self._notify_window, ResultEvent('unpuzzled'))
         
         
class UnpuzzleGUI(wx.Frame):        

    def __init__(self, parent, title): 
        
        super(UnpuzzleGUI, self).__init__(parent, title=title)

        self.InitUI()

        self.Centre()
        self.Show()

    def InitUI(self):
      
        self.panel = wx.Panel(self)
        self.sizer = wx.GridBagSizer(6, 2)

        name_ver = wx.StaticText(self.panel,
                              label="Unpuzzler V3 - 1/09/2013")
        self.sizer.Add(name_ver,
                  pos=(0, 0),
                  flag=wx.ALL|wx.ALIGN_LEFT,
                  border=15)

        line = wx.StaticLine(self.panel)
        self.sizer.Add(line,
                  pos=(1, 0),
                  span=(1,2),
                  flag=wx.EXPAND|wx.ALL,
                  border=0)

        base_text = wx.StaticText(self.panel,
                              label="Base STL: ")
        self.sizer.Add(base_text,
                  pos=(2, 0),
                  span=(1,1),
                  flag=wx.ALIGN_RIGHT)

        self.file_picker = wx.FilePickerCtrl(parent=self.panel,        
                                    path=wx.EmptyString)
        self.sizer.Add(self.file_picker,
                  pos=(2, 1),
                  span=(1,1),
                  flag=wx.ALIGN_LEFT,
                  border=10)
                  
        #self.checkbox = wx.CheckBox(parent=self.panel,        
        #                            label="Open file in NetFabb on Completion")
        #self.checkbox.SetValue(True)
        #self.sizer.Add(self.checkbox,
        #          pos=(3, 0),
        #          span=(1,2),
        #          flag=wx.ALL|wx.ALIGN_LEFT,
        #          border=10)                  

        self.vertex_tolerance_value = 5
        #self.tolerance_input = SpinCtrl(parent=self.panel, value = self.vertex_tolerance_value, size=(50,22))
        self.tolerance_input = SpinCtrl(parent=self.panel, size=(80,25), initial = self.vertex_tolerance_value, min = 1, max = 10000000)
        self.sizer.Add(self.tolerance_input, pos=(3,1), flag=wx.LEFT|wx.ALIGN_LEFT, border = 5, span=(1,1))
        self.sizer.Add(wx.StaticText(self.panel, label = "Vertex count tolerance:"), pos=(3, 0), flag=wx.ALIGN_RIGHT)


        self.radius_factor_input = FloatSpin(parent = self.panel, value = 1.0, increment = 0.1, digits = 2)
        self.sizer.Add(self.radius_factor_input, pos=(4,1), flag=wx.LEFT|wx.ALIGN_LEFT, border = 5, span=(1,1))
        self.sizer.Add(wx.StaticText(self.panel, label = "Camera distance:"), pos=(4, 0), flag=wx.ALIGN_RIGHT)

        go_button = wx.Button(self.panel,
                            size=wx.Size( 150, 50),
                            label='\nUnpuzzle!\n')
        go_button.Bind( wx.EVT_BUTTON, self.unpuzzle)
        self.sizer.Add(go_button,
                  pos=(5, 0),
                  span=(2,2),
                  flag=wx.ALIGN_CENTER|wx.ALL,
                  border=2)
                  
        self.gauge_range = 100
        self.ProgPanel = wx.Gauge(self.panel,
                                   range=self.gauge_range)
        self.sizer.Add(self.ProgPanel,
                  pos=(7, 0),
                  span=(1,2),
                  flag=wx.ALIGN_CENTER|wx.EXPAND|wx.ALL,
                  border=2)

         
        self.Prog_label = wx.StaticText(self.panel,
                                        label=" Nothing to report.")
        self.sizer.Add(self.Prog_label,
                  pos=(8, 0),
                  span=(1,2),
                  flag=wx.ALIGN_CENTER|wx.EXPAND|wx.ALL,
                  border=2)
        
        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        # And indicate we don't have a worker thread yet
        self.worker = None
         
        EVT_RESULT(self,self.OnResult)

    def unpuzzle(self,parent):
        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        
        unpuzzle_path_file = self.file_picker.GetTextCtrlValue()
        
        if not self.worker and unpuzzle_path_file <> '':
            
            self.ProgPanel.SetValue(10)
            self.Prog_label.SetLabel(" Configuring Environment...")
            
            path_separator = "/"
            if IS_WINDOWS:
              path_separator = "\\"
            self.unpuzzle_path = str(os.path.dirname(os.path.realpath(unpuzzle_path_file)))+path_separator
            self.unpuzzle_file_name = str(os.path.basename(unpuzzle_path_file))
            
            os.chdir(self.unpuzzle_path)
            
            self.unpuzzle_script_file = sys.path[0] + path_separator + "unpuzzler_for_ui.py"
            
            d = dict(os.environ)   # Make a copy of the current environment
            
            # Set environment variables
            d['unpuzzle_path'] = self.unpuzzle_path
            d['unpuzzle_file_name'] = self.unpuzzle_file_name
            d['vertex_tolerance'] = str(self.tolerance_input.GetValue())
            d['radius_factor'] = str(self.radius_factor_input.GetValue())
            # d['unpuzzle_file_name_result'] = self.unpuzzle_file_name_result
           
            self.ProgPanel.SetValue(40)
            self.Prog_label.SetLabel(" Unpuzzling...(wait for it)")
            
            os.chdir(blender_directory)
            
            self.worker = Unpuzzle_Thread(self,
                                          self.unpuzzle_path,
                                          self.unpuzzle_script_file,
                                          d)
                                  
        
    def OnResult(self, event):
        """Show Result status."""
        if event.data == 'unpuzzled':
            os.chdir(self.unpuzzle_path)
            self.ProgPanel.SetValue(100)
            self.Prog_label.SetLabel(" Unpuzzled: "+self.unpuzzle_file_name)

            #if self.checkbox.GetValue():
            #    subprocess.Popen("start "+self.unpuzzle_file_name_result,
            #                    shell=True)
            fname = self.unpuzzle_file_name.split('.')[0]
            if IS_WINDOWS:
                subprocess.Popen([firefox_path, "file:///" + self.unpuzzle_path + "html/" + fname + "/" + fname + ".html"])
            else:
                subprocess.Popen(["open", self.unpuzzle_path + "html/" + fname + "/" + fname + ".html"])
        else:
            self.Prog_label.SetLabel(" Something went horribly wrong :(")
        self.worker = None
        


if __name__ == '__main__':
    app = wx.App()
    UnpuzzleGUI(None, title="Unpuzzler V3")
    app.MainLoop()
