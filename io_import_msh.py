bl_addon_info = {
    "name": "Import Orbiter mesh (.msh)",
    "author": "vlad32768",
    "version": (1,0),
    "blender": (2, 5, 4),
    "api": 31236,
    "category": "Import/Export",
    "location": "File > Import > Orbiter mesh (.msh)",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/My_Script",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=#&group_id=#&atid=#",
    "description": """\
This script imports Orbiter mesh file into Blender
"""}

import bpy

import io #file i/o


def test_create_mesh():
    '''Test function that creates mesh'''
    name="Test"
    verts=((0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,1,1))
    faces=((0,1,3,2),(2,3,4))


    me = bpy.data.meshes.new(name+"Mesh")
    ob = bpy.data.objects.new(name, me)
    ob.location =(0,0,0) #origin
    #ob.draw_name = True
    # Link object to scene
    bpy.context.scene.objects.link(ob)
    # Create mesh from given verts, edges, faces. Either edges or
    # faces should be [], or you ask for problems
    me.from_pydata(verts,[], faces)
    # Update mesh with new data
    me.update(calc_edges=True)
    return ob


def load_msh(filename,orbiterpath):
    '''Read MSH file'''
    print("filepath=",filename,"orbiterpath=",orbiterpath)
    test_create_mesh()

    file=open(filename,"r")
    s=file.readline();
    if s!='MSHX1\n':
        print("This file is not orbiter mesh: ",s)
        return
    else:
        print("Orbiter mesh format detected ")
    
    while s!='':
        s=file.readline()
        print(s,end='')
    
    #file 
    file.close()

    return{"FINISHED"}

#for operator class properties
from bpy.props import *

class IMPORT_OT_msh(bpy.types.Operator):
    '''Import MSH Operator.'''
    bl_idname= "import_scene.msh"
    bl_label= "Import MSH"
    bl_description= "Import an Orbiter mesh (.msh)"
    bl_options= {'REGISTER', 'UNDO'}
    
    filepath= StringProperty(name="File Path", description="Filepath used for importing the MSH file", maxlen=1024, default="")
    
    #orbiterpath default for testing
    orbiterpath= StringProperty(name="Orbiter Path", description="Orbiter spacesim path", maxlen=1024, default="~/programs/orbiter", subtype="DIR_PATH")

    def execute(self,context):
        print("execute")
        load_msh(self.filepath,self.orbiterpath)
        return{"FINISHED"}

    def invoke(self,context,event):
        print("invoke")
        wm=context.window_manager
        wm.add_fileselect(self)
        return {"RUNNING_MODAL"}




def menu_function(self,context):
    self.layout.operator(IMPORT_OT_msh.bl_idname, text="Orbiter Mesh (.msh)")
    

def register():
    #bpy.types.register(MyOperator)
    print("registering...")
    bpy.types.INFO_MT_file_import.append(menu_function)
 
def unregister():
    print("unregistering...")
    #bpy.types.unregister(MyOperator)
    bpy.types.INFO_MT_file_import.remove(menu_function)
 
if __name__ == "__main__":
    register()

