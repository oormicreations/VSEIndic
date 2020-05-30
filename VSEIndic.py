# VS Parallel Render by Oormi Creations
#http://oormi.in


bl_info = {
    "name": "VSE Indic",
    "description": "Renders Indic Text in VSE",
    "author": "Oormi Creations",
    "version": (0, 1, 1),
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


# Functions ############################################

def ShowMessageBox(message = "", title = "VSE Indic Says...", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def popfonts(self, context):
    val = []
    for f in range(0,len(bpy.data.fonts)):
        b = (bpy.data.fonts[f].name_full, bpy.data.fonts[f].name, str(f))
        #print(b)
        val.append(b)
    return val


def createindictext(tool, update, imp):
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
    seq.use_translation = tool.in_off
    seq.transform.offset_x = (bpy.context.scene.render.resolution_x)/2 - (image.width/2) 
    seq.transform.offset_y = (bpy.context.scene.render.resolution_y)/2 - (image.height/2)

    #set current frame to position next image
    if imp is not None:
        bpy.context.scene.frame_current = bpy.context.scene.frame_current+tool.in_dur

    
    return fname



def importtext(tool, txtfile):
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
        

class OBJECT_PT_InHelpPanel(bpy.types.Panel):

    bl_label = "Help"
    bl_idname = "OBJECT_PT_VSEIndicHelp"
    bl_category = "VSE Indic"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_VSEIndic"
    bl_order = 2
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
    OBJECT_PT_InHelpPanel
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