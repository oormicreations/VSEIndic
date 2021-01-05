# VS Parallel Render by Oormi Creations
#http://oormi.in


bl_info = {
    "name": "VSE Indic",
    "description": "Renders Indic Text in VSE",
    "author": "Oormi Creations",
    "version": (0, 2, 3),
    "blender": (2, 80, 0),
    "location": "Video Sequencer > VSE Indic",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/oormicreations/VSEIndic",
    "tracker_url": "https://github.com/oormicreations/VSEIndic",
    "category": "Sequencer"
}

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       IntVectorProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

import os
#import stat
from bpy import context
import codecs
#import shutil
import platform
from datetime import datetime
import pyvips
import math
from time import time
from itertools import chain
from math import *

# Functions ############################################

def ShowMessageBox(message = "", title = "VSEIndic Says...", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def SaveCheck():
    if len(bpy.context.blend_data.filepath)>0:
        return True

    ShowMessageBox("Please save the blend file first")
    return False

def setpixel(img,x,y,color, width):
    offs = (x + int(y*width)) * 4
    if offs >= len(img):
        return img
    for i in range(4):
        img[offs+i] = color[i]
    return img

def blendpixel(img,x,y,color, width):
    offs = (x + int(y*width)) * 4
    if offs >= len(img):
        return img
    for i in range(4):
        img[offs+i] += color[i]
    return img


def genCompGuides(pix, w, h, sz, cen, gold, third):
    s = int(sz/2)
    r = sz%2
    #print(s, r)
    if cen:
        color = (0.5, 0.0, 0.0, 1.0 )
        for z in range(-s, s+r):
            for x in range(0,h):
                pix = setpixel(pix, int(w/2) + z, x, color, w)
        
        for z in range(-s, s+r):
            for x in range(0,w):
                pix = setpixel(pix, x, int(h/2) + z, color, w)
    
    if third:    
        color = (0.0, 0.5, 0.0, 1.0 )
        for z in range(-s, s+r):
            for x in range(0,h):
                pix = setpixel(pix, int(w/3) + z, x, color, w)
                pix = setpixel(pix, int(2*w/3) + z, x, color, w)
                
        for z in range(-s, s+r):
            for x in range(0,w):
                pix = setpixel(pix, x, int(h/3) + z, color, w)
                pix = setpixel(pix, x, int(2*h/3) + z, color, w)

    if gold:
        color = (0.5, 0.5, 0.0, 1.0 )
        gw = int(w/1.618033987)
        for z in range(-s, s+r):
            for x in range(0,h):
                pix = setpixel(pix, gw + z, x, color, w)
                pix = setpixel(pix, w - gw + z, x, color, w)

        gh = int(h/1.618033987)
        for z in range(-s, s+r):
            for x in range(0,w):
                pix = setpixel(pix, x, gh + z, color, w)
                pix = setpixel(pix, x, h - gh + z, color, w)

    return pix

def genvig(pix, w, h, sz, dark, corner, vcol):
    
    if corner:
        sz = sqrt(sz)/7.5
        max = pow(w*h/4, dark)
        for x in range(0, int(w/2)+1):
            for y in range(0,int(h/2)+1):
                fac = pow(x*y, dark/sz)/max
                if fac<1.0:#speeds up 2X
                    color = (vcol[0], vcol[1], vcol[2], 1 - fac)
                    pix = setpixel(pix, x, y, color, w)
                    pix = setpixel(pix, x, h-y, color, w)
                    pix = setpixel(pix, w-x, y, color, w)
                    pix = setpixel(pix, w-x, h-y, color, w)

    else:
        sz = sz*h/200
        for z in range(0, int(sz)):
            color = (vcol[0], vcol[1], vcol[2], dark*(1.0-z/sz) )
            for x in range(0,h):
                pix = setpixel(pix, z, x, color, w)
                pix = blendpixel(pix, w-z, x, color, w)

        for z in range(0, int(sz)):
            color = (vcol[0], vcol[1], vcol[2], dark*(1.0-z/sz) )
            for x in range(0,w):
                pix = blendpixel(pix, x, z, color, w)
                pix = blendpixel(pix, x, h-z, color, w)    
    
    return pix


def genshape(pix, w, h, col, round):
    
    round = h*round/200
    if h>w:
        round = w*round/200
    r = round*round

    for x in range(0, int(w)+1):
        for y in range(0,int(h)+1):
            color = (col[0], col[1], col[2], 1)
            pix = setpixel(pix, x, y, color, w)
                
    for x in range(0, int(round)+1):
        for y in range(0,int(round)+1):
            x1 = x- round
            y1 = y- round
            fac = (x1*x1 + y1*y1)
            if fac>r:
                color = (col[0], col[1], col[2], 0)
                pix = setpixel(pix, x, y, color, w)
                pix = setpixel(pix, w-x, y, color, w)
                pix = setpixel(pix, x, h-y, color, w)
                pix = setpixel(pix, w-x, h-y, color, w)
            
            #antialiasing
            '''
            if fac<r+160 and fac>r-160:
                alfa = (r-fac)/fac
                print(alfa)
                color1 = (col[0], col[1], col[2], alfa*15)
                pix = setpixel(pix, x, y, color1, w)
            '''

    return pix

def createshape(intool, update):
    if not SaveCheck():
        return None

    dir = bpy.path.abspath("//")
    outdir = dir + "vseindic"
    if not os.path.exists(outdir):
        os.mkdir(outdir)
            
    today = datetime.now()
    fname = today.strftime("%Y%m%d%H%M%S") + ".png"
    
    if update:
        seq = bpy.context.scene.sequence_editor.active_strip
        if seq is not None:
            print(seq.type)
            if seq.type != "IMAGE":
                ShowMessageBox("Please select a strip of type 'Image'")
                return 
        else:
            ShowMessageBox("Please select a strip")
            return
            
        fname = seq.elements[0].filename

    iname  = 'VSEIndicImageSh'
    iwidth  = intool.in_shw #*bpy.context.scene.render.resolution_x/100
    iheight = intool.in_shh #*bpy.context.scene.render.resolution_y/100
    ialpha = True


    oldImage = bpy.data.images.get(iname, None)
    if oldImage:
        bpy.data.images.remove(oldImage)

    image = bpy.data.images.new(iname, iwidth, iheight, alpha=ialpha)

    start = time()
    pixels = list(image.pixels)
    pixels = [0]*len(pixels)
        
    image.pixels = genshape(pixels, iwidth, iheight, intool.in_shcolor, intool.in_shr)
    image.update()

    print('T: %f seconds' % (time() - start))
    
    showimage(image)
    
    image.filepath_raw = "//vseindic/" + fname
    image.file_format = 'PNG'
    image.save()

    dir = bpy.path.abspath("//")
    outdir = dir + "vseindic"
    if not os.path.exists(outdir):
        os.mkdir(outdir)
        
    if not update:
        bpy.ops.sequencer.image_strip_add(directory= outdir + "/", 
            files=[{"name":fname, "name":fname}], 
            frame_start=bpy.context.scene.frame_current, 
            frame_end=bpy.context.scene.frame_current+intool.in_dur, 
            channel=intool.in_track)
            
    else:
        bpy.ops.sequencer.refresh_all()
        
    seq = bpy.context.scene.sequence_editor.active_strip
    seq.frame_final_duration = intool.in_dur
    seq.use_translation = True
    seq.transform.offset_x = (bpy.context.scene.render.resolution_x)/2 - (iwidth/2)
    seq.transform.offset_y = (bpy.context.scene.render.resolution_y)/2 - (iheight/2)



def popfonts(self, context):
    val = []
    for f in range(0,len(bpy.data.fonts)):
        b = (bpy.data.fonts[f].name_full, bpy.data.fonts[f].name, str(f))
        #print(b)
        val.append(b)
    return val


def createindictext(tool, update, imp):
    if not SaveCheck():
        return None
        
    dir = bpy.path.abspath("//")
    outdir = dir + "vseindic"
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    today = datetime.now()
    #fname = today.strftime("%d/%m/%Y %H:%M:%S")
    fname = today.strftime("%Y%m%d%H%M%S") + ".png"
    
    if update:
        seq = bpy.context.scene.sequence_editor.active_strip
        fname = seq.elements[0].filename
        
    if imp is not None:
        fname = imp + ".png"
        
    fpath = dir + "vseindic/" + fname
    
    w = bpy.context.scene.render.resolution_x * tool.in_width /100.0
    f = tool.in_fontlist
    if f==None or f=="":
        f = "Bfont"
    
    txt = tool.in_text
    if txt == "":
        txt = "<i><u>Indic</u></i> इंडिक സൂചിപ്പിക്കുക\n ਸੰਕੇਤ குறி インド語 מציין"
    txt = txt.replace("\\n", "\n")
    #print(txt) #will not print correctly in linux terminal
        
    image = pyvips.Image.text(txt, width=w,align=tool.in_align, font=f, dpi=tool.in_sz)
    image = image.ifthenelse([255, 255, 255, 255], [0, 0, 0, 0], blend=True)
    
    if tool.in_blur>0:
        image = image.gaussblur(tool.in_blur)
    image = image.copy(interpretation="srgb")
    image = image*[tool.in_color[0], tool.in_color[1], tool.in_color[2], tool.in_color[3]]
    #image = image*1.75
    #print(image.bands)

    image.write_to_file(fpath)

    if not update:
        bpy.ops.sequencer.image_strip_add(directory= outdir + "/", 
            files=[{"name":fname, "name":fname}], 
            frame_start=bpy.context.scene.frame_current, 
            frame_end=bpy.context.scene.frame_current+tool.in_dur, 
            channel=tool.in_track)
    
    
    #auto center and duration update
    seq = bpy.context.scene.sequence_editor.active_strip
    seq.frame_final_duration = tool.in_dur
    
    if bpy.app.version[1]<92:
        seq.use_translation = tool.in_off
        seq.transform.offset_x = (bpy.context.scene.render.resolution_x)/2 - (image.width/2) 
        seq.transform.offset_y = (bpy.context.scene.render.resolution_y)/2 - (image.height/2)
    else:
        seq.transform.scale_x = image.width/bpy.context.scene.render.resolution_x
        seq.transform.scale_y = seq.transform.scale_x


    #set current frame to position next image
    if imp is not None:
        bpy.context.scene.frame_current = bpy.context.scene.frame_current+tool.in_dur

    
    return fname



def importtext(tool, txtfile):
    if not SaveCheck():
        return None
    
    print("~Txtfile~",txtfile)
    prefix = bpy.path.basename(txtfile)

    sep = tool.in_sep
    if tool.in_sep == "\\n":
        sep = '\n'
        print("~Sep~",sep)
        
    temp = codecs.open(txtfile, "r", "utf-8")
    tstr = temp.read()
    temp.close()
    lines = tstr.split(sep, 999)
    print(lines)
    
    if len(lines)<2:
        if lines[0] == "":
            lines = ["The file seems to be empty!"]

    #calc duration from range
    if tool.in_fit:
        bpy.context.scene.frame_current = tool.in_fit1
        tool.in_dur = 1 + (abs(tool.in_fit2 - tool.in_fit1))/len(lines)
        if tool.in_dur < 1:
            tool.in_dur = 1
    
    for n in range(0,len(lines)):
        lines[n] = lines[n].strip()
        lines[n] = lines[n].strip('\n')
        
        print(n,">>>>", lines[n])
        if lines[n] != "" or lines[n] != " " or lines[n] != "\n":
            tool.in_text = lines[n]
            id = str(n + 1)
            createindictext(tool, False, prefix + "_" + id)

def showimage(image):
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image


# Operators ###########################################

class CCI_OT_CCreateIndic(bpy.types.Operator):
    bl_idname = "create.indic"
    bl_label = "Create Indic"
    bl_description = "Create indic text."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool
        createindictext(intool, False, None)
        
        return{'FINISHED'}

class CUC_OT_CUpdateCurrent(bpy.types.Operator):
    bl_idname = "update.current"
    bl_label = "Update Current"
    bl_description = "Update current text and overwrite it."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool
        
        seq = bpy.context.scene.sequence_editor.active_strip
        if seq is not None:
            if seq.type == "IMAGE":
                createindictext(intool, True, None)
            else:
                ShowMessageBox("Please select a strip of type 'Image'")
        else:
            ShowMessageBox("Please select a strip")
        
        return{'FINISHED'}

    
class COF_OT_COpenFont(bpy.types.Operator):
    bl_idname = "open.fontfile"
    bl_label = "Scan file for return"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        print(self.filepath)
        infont = bpy.data.fonts.load(self.filepath)
        print(infont.name_full)
        context.scene.in_tool.in_fontlist = infont.name
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}    


class CIM_OT_CImport(bpy.types.Operator):
    bl_idname = "import.text"
    bl_label = "Import Text"
    bl_description = "Import text from a file"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool
        importtext(intool, self.filepath)
        
        return{'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}    

class CCG_OT_CCreateGuides(bpy.types.Operator):
    bl_idname = "create.guides"
    bl_label = "Create Guides"
    bl_description = "Create guide lines strip."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool

        if not SaveCheck():
            return {'FINISHED'}
                
        iname  = 'VSEIndicImage'
        iwidth  = bpy.context.scene.render.resolution_x
        iheight = bpy.context.scene.render.resolution_y
        ialpha = True
        linesz = intool.in_linesz #px

        oldImage = bpy.data.images.get(iname, None)
        if oldImage:
            bpy.data.images.remove(oldImage)

        image = bpy.data.images.new(iname, iwidth, iheight, alpha=ialpha)

        start = time()
        pixels = list(image.pixels)
        pixels = [0]*len(pixels)
            
        image.pixels = genCompGuides(pixels, iwidth, iheight, linesz, intool.in_gcenter, intool.in_ggolden, intool.in_gthirds)
        image.update()

        print('T: %f seconds' % (time() - start))
        
        showimage(image)
        
        dir = bpy.path.abspath("//")
        outdir = dir + "vseindic"
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        
        image.filepath_raw = "//vseindic/VSEIndicGuides.png"
        image.file_format = 'PNG'
        image.save()

        dir = bpy.path.abspath("//")
        outdir = dir + "vseindic"
        if not os.path.exists(outdir):
            os.mkdir(outdir)
            
        seq = None
        try:
            seq = bpy.context.scene.sequence_editor.sequences_all['VSEIndicGuides.png']
        except:
            pass
                    
        if seq is None:
            bpy.ops.sequencer.image_strip_add(directory= outdir + "/", 
                files=[{"name":"VSEIndicGuides.png", "name":"VSEIndicGuides.png"}], 
                frame_start=bpy.context.scene.frame_start, 
                frame_end=bpy.context.scene.frame_end)
        else:
            bpy.ops.sequencer.refresh_all()
                                
        return{'FINISHED'}
    

class CCV_OT_CCreateVig(bpy.types.Operator):
    bl_idname = "create.vig"
    bl_label = "Create Vignette"
    bl_description = "Create vignette strip."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool
        
        if not SaveCheck():
            return {'FINISHED'}
                
        iname  = 'VSEIndicImageVig'
        iwidth  = bpy.context.scene.render.resolution_x
        iheight = bpy.context.scene.render.resolution_y
        ialpha = True
        vigsz = intool.in_vigsz
        dark = intool.in_vigdark/75
        corner = intool.in_vigtype == 'COR'
        vigcolor = intool.in_vigcolor

        oldImage = bpy.data.images.get(iname, None)
        if oldImage:
            bpy.data.images.remove(oldImage)

        image = bpy.data.images.new(iname, iwidth, iheight, alpha=ialpha)

        start = time()
        pixels = list(image.pixels)
        pixels = [0]*len(pixels)
            
        image.pixels = genvig(pixels, iwidth, iheight, vigsz, dark, corner, vigcolor)
        image.update()

        print('T: %f seconds' % (time() - start))
        
        showimage(image)
        
        dir = bpy.path.abspath("//")
        outdir = dir + "vseindic"
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        
        image.filepath_raw = "//vseindic/VSEIndicVig.png"
        image.file_format = 'PNG'
        image.save()

        dir = bpy.path.abspath("//")
        outdir = dir + "vseindic"
        if not os.path.exists(outdir):
            os.mkdir(outdir)
            
        seq = None
        try:
            seq = bpy.context.scene.sequence_editor.sequences_all['VSEIndicVig.png']
        except:
            pass
                    
        if seq is None:
            bpy.ops.sequencer.image_strip_add(directory= outdir + "/", 
                files=[{"name":"VSEIndicVig.png", "name":"VSEIndicVig.png"}], 
                frame_start=bpy.context.scene.frame_start, 
                frame_end=bpy.context.scene.frame_end)
        else:
            bpy.ops.sequencer.refresh_all()
                                
        return{'FINISHED'}

class CCS_OT_CCreateShape(bpy.types.Operator):
    bl_idname = "create.shape"
    bl_label = "Create Shape"
    bl_description = "Create Shapes."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool
        createshape(intool, False)
        

        return{'FINISHED'}

class CUS_OT_CUpdateShape(bpy.types.Operator):
    bl_idname = "update.shape"
    bl_label = "Update Shape"
    bl_description = "Update existing shapes."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool
        createshape(intool, True)
        

        return{'FINISHED'}

class CCI_OT_CCreateIndex(bpy.types.Operator):
    bl_idname = "create.index"
    bl_label = "Create Index"
    bl_description = "Create Time Index from a track."

    def execute(self, context):
        scene = context.scene
        intool = scene.in_tool

        fps = scene.render.fps / scene.render.fps_base

        indexitem = None
        indexlist = []

        seq = bpy.context.scene.sequence_editor.sequences_all
        for s in seq:
            if s.type == 'TEXT':
                if s.channel == intool.in_indtrack:
                    #print(s.frame_start, s.text)
                    indexitem = (s.frame_final_start/fps, s.text)
                    indexlist.append(indexitem)

        indexlist.sort(key = lambda x: x[0])

        for i in indexlist:
            min = i[0]/60
            #print(int(min),':', int((min%1)*60), i[1])
            print("%02d:%02d %s" %(int(min), int((min%1)*60), i[1]))
                

        return{'FINISHED'}    
    
# Panel ###############################################
    
class OBJECT_PT_InPanel(bpy.types.Panel):

    bl_label = "VSE Indic"
    bl_idname = "OBJECT_PT_VSEIndic"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_order = 0
#    bl_context = "objectmode"

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        layout.prop(intool, "in_text")
        row = layout.row(align=True)
        row.prop(intool, "in_sz")
        row.prop(intool, "in_align")
        row = layout.row(align=True)
        row.prop(intool, "in_width")
        row.prop(intool, "in_dur")
        row.prop(intool, "in_track")
        
        row = layout.row(align=True)
        row.prop(intool, "in_fontlist", icon='FILE_FONT')
        row.operator("open.fontfile", text = "Open", icon='FILEBROWSER')

        row = layout.row(align=False)
        row.prop(intool, "in_color")
        row.prop(intool, "in_blur")
        
        layout.label(text = " ")
        layout.prop(intool, "in_off")

        layout.operator("create.indic", text = "Create Indic Text", icon='TEXT')
        layout.operator("update.current", text = "Update Current Text", icon='FILE_TICK')


class OBJECT_PT_InImpPanel(bpy.types.Panel):

    bl_label = "Import From File"
    bl_idname = "OBJECT_PT_VSEIndicImp"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 1

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        layout.prop(intool, "in_fit")
        row = layout.row(align=True)
        row.prop(intool, "in_fit1")
        row.prop(intool, "in_fit2")
        
        row = layout.row(align=True)
        row.prop(intool, "in_sep")
        row.operator("import.text", text = "Import Text", icon='TEXT')


class OBJECT_PT_GuidesPanel(bpy.types.Panel):

    bl_label = "Guides"
    bl_idname = "OBJECT_PT_VSEIndicGuides"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 2

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        
        row = layout.row(align=True)
        row.prop(intool, "in_gcenter")
        row.prop(intool, "in_ggolden")
        row.prop(intool, "in_gthirds")
        
        row = layout.row(align=True)
        row.prop(intool, "in_linesz")        
        row.operator("create.guides", text = "Create Guides", icon='ALIGN_FLUSH')



class OBJECT_PT_VigPanel(bpy.types.Panel):

    bl_label = "Vignette"
    bl_idname = "OBJECT_PT_VSEIndicVig"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 3

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        row = layout.row(align=True)
        row.prop(intool, "in_vigtype")
        row.prop(intool, "in_vigcolor")        
        
        row = layout.row(align=True)
        row.prop(intool, "in_vigdark")
        row.prop(intool, "in_vigsz")
        
        layout.operator("create.vig", text = "Create Vignette", icon='CLIPUV_HLT')

class OBJECT_PT_ShapePanel(bpy.types.Panel):

    bl_label = "Shapes"
    bl_idname = "OBJECT_PT_VSEIndicShape"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 4

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        row = layout.row(align=True)
        row.prop(intool, "in_shw")
        row.prop(intool, "in_shh")        
        
        row = layout.row(align=True)
        row.prop(intool, "in_shcolor")
        row.prop(intool, "in_shr")
        
        layout.operator("create.shape", text = "Create Shape", icon='SOLO_ON')
        layout.operator("update.shape", text = "Update Shape", icon='SOLO_OFF')

class OBJECT_PT_IndexPanel(bpy.types.Panel):

    bl_label = "Index"
    bl_idname = "OBJECT_PT_VSEIndicIndex"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 5

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        row = layout.row(align=True)
        row.prop(intool, "in_indtrack")
        #row.prop(intool, "in_shr")
        
        layout.operator("create.index", text = "Create Index", icon='TEXT')


        

class OBJECT_PT_InHelpPanel(bpy.types.Panel):

    bl_label = "Help"
    bl_idname = "OBJECT_PT_VSEIndicHelp"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 6
#    bl_options = "DEFAULT_CLOSED"
#    bl_context = "objectmode"

    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intool = scene.in_tool

        row = layout.row(align=True)
        row.operator("wm.url_open", text="Help | Source | Updates", icon='QUESTION').url = "https://github.com/oormicreations/VSEIndic"


class CCProperties(PropertyGroup):
    
    in_text: StringProperty(
        name = "Input Text",
        description = "Paste or type your Indic text here",
        default = "<i><u>Indic</u></i> इंडिक സൂചിപ്പിക്കുക\n ਸੰਕੇਤ குறி インド語 מציין"
      )

    in_sz: IntProperty(
        name = "Size",
        description = "Text Size",
        default = 400,
        min = 10,
        max = 2000
      )

    in_width: IntProperty(
        name = "Width",
        description = "Text width in % of video width",
        default = 50,
        min = 10,
        max = 100
      )

    in_dur: IntProperty(
        name = "Duration",
        description = "Time duration in frames",
        default = 120,
        min = 1,
        max = 10000
      )
      
    in_track: IntProperty(
        name = "Track",
        description = "Track number",
        default = 1,
        min = 1,
        max = 32
      )
            
    in_blur: FloatProperty(
        name = "Blur",
        description = "Blur for shadows etc",
        default = 0,
        min = 0,
        max = 10
      )
      
    in_off: BoolProperty(
        name = "Auto Center",
        description = "Auto offset text so that it is centered",
        default = True
    )

    in_upd: BoolProperty(
        name = "Update Current",
        description = "Overwrites the current text with updated parameters",
        default = False
    )
    
    in_fontlist: EnumProperty(
        items = popfonts,
        name = ""
    )    

    in_align: EnumProperty(
        items = [("low","Left",""),("centre","Centre",""),("high","Right","")],
        default = "centre",
        name = ""
    ) 

    in_sep: StringProperty(
        default = ";",
        name = "Separator"
    ) 
    
    in_color: FloatVectorProperty(
         name = "Color",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (1.0,1.0,1.0,1.0)
     )

    in_fit: BoolProperty(
        name = "Fit in range:",
        description = "Fit imported text in a given frame range",
        default = True
    )

    in_fit1: IntProperty(
        name = "",
        description = "Frame range start",
        default = 1,
        min = 1
      )
      
    in_fit2: IntProperty(
        name = "",
        description = "Frame range end",
        default = 1000,
        min = 1
      )

    in_gcenter: BoolProperty(
        name = "Center Cross",
        description = "Show center cross guides",
        default = True
    )

    in_ggolden: BoolProperty(
        name = "Golden Ratio",
        description = "Show golden ratio guides",
        default = True
    )

    in_gthirds: BoolProperty(
        name = "Thirds",
        description = "Show thirds guides",
        default = True
    )

    in_linesz: IntProperty(
        name = "Line Size",
        description = "Guide line size in pixels",
        default = 3,
        min = 1,
        max = 100
      )

    in_vigdark: FloatProperty(
        name = "Density",
        description = "Darkness of the vignette border",
        default = 15,
        min = 0.1,
        max = 100.0
      )

    in_vigcolor: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.0,0.0,0.0,1.0)
     )

    in_vigsz: FloatProperty(
        name = "Size",
        description = "Vignette size in percent of image width",
        default = 30,
        min = 1,
        max = 100
      )

    in_vigtype: EnumProperty(
        items = [("BOX","Box",""),("COR","Corner","")],
        default = "COR",
        name = "Type"
    ) 

    in_shw: IntProperty(
        name = "Width",
        description = "Width of the shape in pixels",
        default = 100,
        min = 1,
        max = 100000
      )

    in_shh: IntProperty(
        name = "Height",
        description = "Height of the shape in pixels",
        default = 100,
        min = 1,
        max = 100000
      )

    in_shr: IntProperty(
        name = "Roundedness",
        description = "Roundedness of the shape in %",
        default = 10,
        min = 0,
        max = 100
      )

    in_shcolor: FloatVectorProperty(
         name = "",
         subtype = "COLOR",
         size = 4,
         min = 0.0,
         max = 1.0,
         default = (0.5,0.0,0.0,1.0)
     )

    in_indtrack: IntProperty(
        name = "Track",
        description = "Track number for index creation",
        default = 1,
        min = 1,
        max = 32
      )

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    OBJECT_PT_InPanel,
    CCProperties,
    CCI_OT_CCreateIndic,
    COF_OT_COpenFont,
    CUC_OT_CUpdateCurrent,
    CIM_OT_CImport,
    OBJECT_PT_InImpPanel,
    OBJECT_PT_InHelpPanel,
    OBJECT_PT_GuidesPanel,
    OBJECT_PT_VigPanel,
    CCG_OT_CCreateGuides,
    CCV_OT_CCreateVig,
    OBJECT_PT_ShapePanel,
    CCS_OT_CCreateShape,
    CUS_OT_CUpdateShape,
    OBJECT_PT_IndexPanel,
    CCI_OT_CCreateIndex
)

def register():
    bl_info['blender'] = getattr(bpy.app, "version")
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.in_tool = PointerProperty(type=CCProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.in_tool



if __name__ == "__main__":
    register()
