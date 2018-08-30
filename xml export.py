import os
import wx
import glob
import datetime
import xml.etree.cElementTree as ET
import xml.etree.ElementTree
import bisect
import numpy as np

def main():
    app = wx.App(False)
    frame = MyFrame(None, 'XML Export')
    app.MainLoop()

def thining(img,img_interval,retain_pt,tie_rays):
    #略
    return retain_pt

def mask(CAM_info):
    x_in = -CAM_info[0]*CAM_info[3]
    y_in = -CAM_info[1]*CAM_info[3]
    x_interval = [x_in]
    y_interval = [y_in]
    for i in xrange(5):
        x_in += ((CAM_info[4])*CAM_info[3]/5)
        x_interval.append(x_in)
        y_in += ((CAM_info[5])*CAM_info[3]/5)
        y_interval.append(y_in)
    x_interval = x_interval[1:-1]
    y_interval = y_interval[1:-1]
    return [x_interval,y_interval]

def xml2im(inputXMLFilePath):
    dirpath = os.path.dirname(inputXMLFilePath)
    XMLfile = os.path.basename(inputXMLFilePath)
    XMLname = os.path.splitext(XMLfile)[0]
    os.path.basename(inputXMLFilePath)
    tree = ET.ElementTree(file=inputXMLFilePath)
    root = tree.getroot()
    photogroup = {}
    photoID = []
    controlpoint_XYZ = {}
    point_xy = {}
    tie_rays = {}
    con_number = 999000001
    tie_number = 555000001
    for name in root.findall('.//Photogroups/Photogroup'):
        CAM = name.find('Name').text
        Width = int(name.find('.//ImageDimensions/Width').text)
        Height = int(name.find('.//ImageDimensions/Height').text)
        FocalLength = "%.3f" % (float(name.find('FocalLength').text)*1000)
        SensorSize = float(name.find('SensorSize').text)
        PixelSize = SensorSize/max([Width,Height])*1000
        PrincipalPoint_x = float(name.find('.//PrincipalPoint/x').text)
        PrincipalPoint_y = float(name.find('.//PrincipalPoint/y').text)
        photogroup[CAM] = [PrincipalPoint_x,PrincipalPoint_y,FocalLength,PixelSize,Width,Height]
        for i in name.findall('Photo'):
            img_id = i.find('Id').text
            img_name = os.path.splitext(os.path.basename(i.find('ImagePath').text))[0]
            photoID.append([img_id,img_name,CAM])
    for ContralPoint in root.findall('.//ControlPoints/ControlPoint'):
        con_Name = ContralPoint.find('Name').text
        for Position in ContralPoint.findall('Position'):
            con_X = "%.6f" % float(Position.find('x').text)
            con_Y = "%.6f" % float(Position.find('y').text)
            con_Z = "%.6f" % float(Position.find('z').text)
        controlpoint_XYZ[con_number] = [con_X,con_Y,con_Z]
        for Measurement in ContralPoint.findall('Measurement'):
            PhotoId = Measurement.find('PhotoId').text
            CAM = [i[2] for i in photoID if i[0] == PhotoId][0]
            con_x = float(Measurement.find('x').text)
            con_x_v = "%.3f" % ((con_x-(photogroup[CAM][0]))*photogroup[CAM][3])
            con_y = float(Measurement.find('y').text)
            con_y_v = "%.3f" % -((con_y-(photogroup[CAM][1]))*photogroup[CAM][3])
            if PhotoId not in point_xy:
                point_xy[PhotoId] = [[con_number,con_x_v,con_y_v]]
            else:
                point_xy[PhotoId].append([con_number,con_x_v,con_y_v])
        con_number += 1
    for TiePoint in root.findall('.//TiePoints/TiePoint'):
        tie_rays[tie_number] = len(TiePoint.findall('Measurement'))
        for Measurement in TiePoint.findall('Measurement'):
            PhotoId = Measurement.find('PhotoId').text
            CAM = [i[2] for i in photoID if i[0] == PhotoId][0]
            tie_x = float(Measurement.find('x').text)
            tie_x_v = "%.3f" % ((tie_x-(photogroup[CAM][0]))*photogroup[CAM][3])
            tie_y = float(Measurement.find('y').text)
            tie_y_v = "%.3f" % -((tie_y-(photogroup[CAM][1]))*photogroup[CAM][3])
            if PhotoId not in point_xy:
                point_xy[PhotoId] = [[tie_number,tie_x_v,tie_y_v]]
            else:
                point_xy[PhotoId].append([tie_number,tie_x_v,tie_y_v])
        tie_number += 1
    #減點
    #略

    #輸出
    im_file = open(os.path.join(dirpath,XMLname+'.im'),'w')
    for [img_id,img_name,CAM] in photoID:
        im_file.write(img_name.rjust(15)+photogroup[CAM][2].rjust(18)+str(1).rjust(11)+'\n')
        if img_id in point_xy:
            for point in point_xy[img_id]:
                if point[0] in retain_pt:
                    im_file.write(str(point[0]).rjust(15)+str(point[1]).rjust(18)+str(point[2]).rjust(18)+str(0).rjust(10)+'\n')
        im_file.write(str(-99).rjust(15)+'\n')
    if controlpoint_XYZ != {}:
        im_file.write(str(0).rjust(15)+'\n')
        for key, value in controlpoint_XYZ.iteritems():
            im_file.write(str(key).rjust(15)+value[0].rjust(18)+value[1].rjust(18)+str(1).rjust(24)+'\n')#16,34,52,76
        im_file.write(str(-99).rjust(15)+'\n')
        im_file.write(str(0).rjust(15)+'\n')
        for key, value in controlpoint_XYZ.iteritems():
            im_file.write(str(key).rjust(15)+value[2].rjust(54)+str(1).rjust(6)+'\n')#16,70,76
        im_file.write(str(-99).rjust(15)+'\n')
    del im_file

def xml2eo(inputXMLFilePath):
    dirpath = os.path.dirname(inputXMLFilePath)
    XMLfile = os.path.basename(inputXMLFilePath)
    XMLname = os.path.splitext(XMLfile)[0]
    os.path.basename(inputXMLFilePath)
    tree = ET.ElementTree(file=inputXMLFilePath)
    root = tree.getroot()
    new_text = open(os.path.join(dirpath,XMLname+'_eo.txt'),'w')
    for name in root.findall('.//Photogroups/Photogroup'):
        CAM = name.find('Name').text
        for i in name.findall('Photo'):
            img_id = i.find('Id').text  
            img_name = os.path.splitext(os.path.basename(i.find('ImagePath').text))[0]
            try:
                omega = i.find('.//Pose/Rotation/Omega').text
                phi = i.find('.//Pose/Rotation/Phi').text
                kappa = i.find('.//Pose/Rotation/Kappa').text
                x = i.find('.//Pose/Center/x').text
                y = i.find('.//Pose/Center/y').text
                z = i.find('.//Pose/Center/z').text
                new_text.write(str(img_name.split('/')[-1])+' '+
                               str(x)+' '+str(y)+' '+str(z)+' '+
                               str(float(omega)+180)+' '+str(float(phi)*-1)+' '+str(float(kappa)*-1)+' '+
                               str(CAM)+
                               '\n')
            except:
                continue
    del new_text

def xml2cam(inputXMLFilePath):
    dirpath = os.path.dirname(inputXMLFilePath)
    XMLfile = os.path.basename(inputXMLFilePath)
    XMLname = os.path.splitext(XMLfile)[0]
    os.path.basename(inputXMLFilePath)
    tree = ET.ElementTree(file=inputXMLFilePath)
    root = tree.getroot()
    new_text = open(os.path.join(dirpath,XMLname+'_cam.txt'),'w')
    for name in root.findall('.//Photogroups/Photogroup'):
        CAM = name.find('Name').text
        if name.find('.//ImageDimensions/Width') != None:
            Width = int(name.find('.//ImageDimensions/Width').text)
        if name.find('.//ImageDimensions/Height') != None:
            Height = int(name.find('.//ImageDimensions/Height').text)
        if name.find('FocalLength') != None:
            FocalLength = "%.3f" % (float(name.find('FocalLength').text))
        if name.find('SensorSize') != None:
            SensorSize = float(name.find('SensorSize').text)
            PixelSize = SensorSize/max([Width,Height])
            SensorSize_x = PixelSize*Width
            SensorSize_y = PixelSize*Height
        if name.find('.//PrincipalPoint/x') != None:
            PrincipalPoint_x = float(name.find('.//PrincipalPoint/x').text)
            ppa_x = -(Width/2-0.5-PrincipalPoint_x)*PixelSize
        if name.find('.//PrincipalPoint/y') != None:
            PrincipalPoint_y = float(name.find('.//PrincipalPoint/y').text)
            ppa_y = (Height/2-0.5-PrincipalPoint_y)*PixelSize
        if name.find('.Distortion/K1') != None:
            K1 = float(name.find('.Distortion/K1').text)
        if name.find('.Distortion/K2') != None:
            K2 = float(name.find('.Distortion/K2').text)
        if name.find('.Distortion/K3') != None:
            K3 = float(name.find('.Distortion/K3').text)
        if name.find('.Distortion/P1') != None:
            P1 = float(name.find('.Distortion/P1').text)
        if name.find('.Distortion/P2') != None:
            P2 = float(name.find('.Distortion/P2').text)
            
        new_text.write(CAM+'\n')
        if name.find('FocalLength') != None:
            new_text.write('focal_length: '+str(FocalLength)+'\n')    
        if name.find('.//PrincipalPoint/x') != None and name.find('.//PrincipalPoint/y') != None:
            new_text.write('ppac: '+str(ppa_x)+'\t'+str(ppa_y)+'\n')
        if name.find('SensorSize') != None:
            new_text.write('film_format: '+str(SensorSize_x)+' '+str(SensorSize_y)+'\n')
            new_text.write('pixel_size: '+str(PixelSize*1000)+'\n')
        if name.find('.//ImageDimensions/Width') != None and name.find('.//ImageDimensions/Height') != None:
            new_text.write('image_size_in_pixels: '+str(Width)+' '+str(Height)+'\n')
        #new_text.write(str(PrincipalPoint_x)+' '+str(PrincipalPoint_y)+'\n')
        if name.find('.Distortion/K1') != None:
            new_text.write('K1: '+str(K1)+'\n')
        if name.find('.Distortion/K2') != None:
            new_text.write('K2: '+str(K2)+'\n')
        if name.find('.Distortion/K3') != None:
            new_text.write('K3: '+str(K3)+'\n')
        if name.find('.Distortion/P1') != None:
            new_text.write('P1: '+str(P1)+'\n')
        if name.find('.Distortion/P2') != None:
            new_text.write('P2: '+str(P2)+'\n')
        new_text.write('\n')
    del new_text

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, #id = wx.ID_ANY, 
                          title = title, size = (500,500))#, 
                          #style = wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER)
        
        ico = wx.Icon('linkfast.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(ico)
        
        self.dirname = ''
        self.counterror = 0
        self.countClear = 0
        
        panel = wx.Panel(self)#, wx.ID_ANY)
        wx.StaticText(parent=panel, label=u" 輸入XML檔: ", pos=(15,10))
        self.a = wx.TextCtrl(parent=panel,pos=(120,10),size=(295,20))
        self.btn1 = wx.Button(parent=panel,label="...",pos=(420,10),size=(40,20))
        self.Bind(wx.EVT_BUTTON, self.OnBtn1, self.btn1)
        
        wx.StaticText(parent=panel, label=u" 輸出格式: ", pos=(15,40))
        self.cb1 = wx.CheckBox(parent=panel, label=u" IM檔 ", pos=(120,40))
        #self.Bind(wx.EVT_CHECKBOX, self.CheckBox1, self.cb1)
        
        self.cb2 = wx.CheckBox(parent=panel, label=u" EO檔 ", pos=(120,70))
        #self.Bind(wx.EVT_CHECKBOX, self.CheckBox2, self.cb2)
        
        self.cb3 = wx.CheckBox(parent=panel, label=u" 相機參數 ", pos=(120,100))
        #self.Bind(wx.EVT_CHECKBOX, self.CheckBox3, self.cb3)
        
        self.btn2 = wx.Button(parent=panel,label=u" 清除訊息 ",pos=(15,130),size=(100,20))
        self.Bind(wx.EVT_BUTTON, self.OnBtn2, self.btn2)
        
        self.btn3 = wx.Button(parent=panel,label=u" 確定 ",pos=(420,130),size=(60,20))
        self.Bind(wx.EVT_BUTTON, self.OnBtn3, self.btn3)
        
        self.txtCtrl = wx.TextCtrl(panel, id=wx.ID_ANY, style=wx.TE_MULTILINE, pos=(10,160), size=(475,330))
        
        self.Show(True)
    def OnBtn1(self,evt):
        global inputfile
        
        dlg = wx.FileDialog(self, u" 選擇XML檔： ",self.dirname, "", "*.xml", wx.OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            if self.dirname[-1] == ':':
                self.dirname = self.dirname + '\\'
            self.a.SetValue(os.path.join(self.dirname, self.filename))
            inputfile = os.path.join(self.dirname, self.filename)
        
    def OnBtn2(self,evt):
        self.txtCtrl.Clear()
        self.counterror = 0
        self.countClear += 1
            
    def OnBtn3(self,evt):
        self.countClear = 0
        if self.a.GetValue() == '' and self.counterror < 5:
            self.txtCtrl.WriteText(u'請輸入XML檔\n')
            self.counterror += 1
        elif self.a.GetValue() == '' and self.counterror >= 5 and self.counterror < 13:
            self.txtCtrl.WriteText(u'請輸入XML檔：按右上方的"..."\n')
            self.counterror += 1
        else:
            if self.cb1.GetValue() == True:
                xml2im(inputfile)
                self.txtCtrl.WriteText(u'IM檔輸出完成!\n')
            if self.cb2.GetValue() == True:
                xml2eo(inputfile)
                self.txtCtrl.WriteText(u'EO檔輸出完成!\n')
            if self.cb3.GetValue() == True:
                xml2cam(inputfile)
                self.txtCtrl.WriteText(u'CAM檔輸出完成!\n')

if __name__ == "__main__":
    main()
