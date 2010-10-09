#################################################################
## Important!
## TODO: When importing, the script changes V to 1-V in UVTex, this should be done in export script
## 
## TODO: Conversion to Orbiter coord system must be done in export script
##
## Conversion from orbiter is: 
##  1. Coordinate system conversion:z=y ; y=-z; x=-x
##  2. Triangle backface flipping: tri[1]<->tri[2]
##  3. UV coord system conversion: v=1-v
##
## Conversion to orbiter should be: z=-y,y=z,x=-x ; tri[1]<-> tri[2] ; v=1-v
##
##################################################################
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
import os
import ntpath

def create_mesh(name,verts,faces,norm,uv):
    '''Function that creates mesh from loaded data'''

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
    
    '''    
    if norm!=[]:
        for i in range(len(norm)):
            me.vertices[i].normal=norm[i]
            print (me.vertices[i].normal)
    '''

    if uv!=[]:
        #Loading UV tex coords
        uvtex=me.uv_textures.new()#create uvset
        print ("lenghts uvtexdata=",len(uvtex.data)," verts=",len(verts))
        for i in range(len(faces)):
            uvtex.data[i].uv1=uv[faces[i][0]]
            uvtex.data[i].uv2=uv[faces[i][1]]
            uvtex.data[i].uv3=uv[faces[i][2]]

    me.update(calc_edges=True)
    return ob


def create_materials(groups,materials,textures,orbiterpath):
    #counting material/texture combinations
    print("Creating materials")
    matpairset=set()
    matpair=[]          # [(mat,tex),[mgroups...]]  Unique mat+tex and corresponding groups
    for n in range(len(groups)):
        l=(groups[n][1],groups[n][2])
        #print(l)
        if l not in matpairset:
            matpairset.add(l)
            matpair.append([l,[]]) #fill unique mat+tex combination
    for n in range(len(groups)):
        l=(groups[n][1],groups[n][2])
        for i in range(len(matpair)):
            if l==matpair[i][0]:
                matpair[i][1].append(n) #fill array of corresponding groups


    print("\nUnique pairs:\n",matpairset)
    print(matpair)
    
    #create textures
    tx=[]
    print("creating textures")
    for n in range(len(textures)):
        v=ntpath.split(textures[n][0])
        print(v);
        fpath=orbiterpath+"/Textures"
        for i in v:
            fpath=fpath+"/"+i
        print (fpath)

        img=bpy.data.images.load(fpath)
        
        tx.append(bpy.data.textures.new(textures[n][1],"IMAGE"))
        tx[n].image=img
        tx[n].use_alpha=True

    
    print("creating materials") 
    n=0
    matt=[]
    for pair in matpair:
        #create material object
        idx_mat=pair[0][0]-1
        idx_tex=pair[0][1]-1
        print("idx_mat=",idx_mat)
        print("mat_name=",materials[idx_mat][0])
        print("diff=",materials[idx_mat][1][:3])
        print("tex=",textures[idx_tex][1],"idx=",idx_tex)
        matt.append(bpy.data.materials.new(materials[idx_mat][0]))
        matt[n].diffuse_color=materials[idx_mat][1][:3]
        #if idx_tex>=0: matt.texture_slots["Tex"].name=textures[idx_tex][1]
        
        #matt[n].add_texture(texture=tx[idx_tex],texture_coordinates='UV',map_to='COLOR')
        if idx_tex>=0:
            mtex=matt[n].texture_slots.add()
            mtex.texture=tx[idx_tex]
            mtex.texture_coords="UV" 
            #mtex.map_colordiff = True
            #mtex.map_alpha = True
            #mtex.map_coloremission = True
            #mtex.map_density = True
            #mtex.mapping = 'FLAT'

        for grp_idx in pair[1]:
            groups[grp_idx][5].data.materials.append(matt[n])
        n=n+1
    

#load mesh function
def load_msh(filename,orbiterpath,convert_coords):
    '''Read MSH file'''
    print("filepath=",filename,"orbiterpath=",orbiterpath)

    file=open(filename,"r")
    s=file.readline();
    if s!='MSHX1\n':
        print("This file is not orbiter mesh: ",s)
        return
    else:
        print("Orbiter mesh format detected ")
    n_groups=0  #N of groups from header
    n_materials=0   #N of mats from header
    n_textures=0    #N of texs from header
    n_grp=0         #real N of groups
    mat=[]          #mats in group (int)
    tex=[]          #texs in group (int)
    groups=[]       #groups description [label(str),mat(int),tex(int),nv(int),nt(int),obj(bpy.data.object)]
    materials=[]    #materials description [name,[diff RGBA],[amb RGBA],[spec RGBAP],[emit RGBA]]
    textures=[]     #[texture filename, texture name]
    while True:
        s=file.readline()
        if s=='': 
            break;
        v=s.split()
        #print (v)
        #------Reading GROUPS section-------------
        if v[0]=="GROUPS":
            print("Reading groups:")
            n_groups=int(v[1]);
            
            n_mat=0; n_tex=0 #group material and texture
            label=""
            while n_grp<n_groups:
                s1=file.readline();
                v1=s1.split()

                #if v1[0]=="NONORMAL":
                #    print("NONORMAL!")
                if v1[0]=="LABEL":
                    label=v1[1]
                if v1[0]=="MATERIAL":
                    n_mat=int(v1[1])  #1..n
                if v1[0]=="TEXTURE":
                    n_tex=int(v1[1])    #1..n

                #Reading geometry
                if v1[0]=="GEOM":
                    vtx=[]
                    tri=[]
                    norm=[]
                    uv=[]
                    
                    nv=int(v1[1])
                    nt=int(v1[2])
                    #print ("Group No:",n_grp," verts=",nv," tris=",nt)
                    for n in range(nv):
                        s2=file.readline();
                        v2=s2.split();
                        #print(v2);
                        if convert_coords:
                            vtx.append([-float(v2[0]),-float(v2[2]),float(v2[1])])# convert from left-handed coord system
                        else: 
                            vtx.append([float(v2[0]),float(v2[1]),float(v2[2])]) #without conversion 
                        if len(v2)>5: #there are normals (not vtx+uvs only)
                            #should I convert the normals?
                            norm.append([float(v2[3]),float(v2[4]),float(v2[5])])
                        if len(v2)==8: #there are normals and uvs
                            if convert_coords:
                                #in Blender, (0,0) is the upper-left corner. 
                                #in Orbiter -- lower-left corner. So I must invert V axis
                                uv.append([float(v2[6]),1.0-float(v2[7])])    
                            else:
                                uv.append([float(v2[6]),float(v2[7])])
                        elif len(v2)==5: #there are only uvs
                            if convert_coords:
                                uv.append([float(v2[3]),1.0-float(v2[4])])    
                            else:
                                uv.append([float(v2[3]),float(v2[4])])

                    for n in range(nt): #read triangles
                        s2=file.readline();
                        v2=s2.split();
                        if convert_coords:
                            tri.append([int(v2[0]),int(v2[2]),int(v2[1])]) #reverted triangle
                        else:
                            tri.append([int(v2[0]),int(v2[1]),int(v2[2])]) #non reverted triangle
                    #print (vtx)
                    #print(norm)
                    n_grp=n_grp+1;
                    if label=='':
                        label="ORBGroup"+str(n_grp)
                    obj=create_mesh(label,vtx,tri,norm,uv)
                    if n_mat!=0:
                        mat.append(n_mat)
                    if n_tex!=0:
                        tex.append(n_tex)
                    groups.append([label,n_mat,n_tex,nv,nt,obj])
                    label=""
        #--------------Reading MATERIALS section-----------------------        
        elif v[0]=="MATERIALS":
            n_materials=int(v[1])
            print("-------Reading Materials section,nmats=",n_materials,"------------")
            #material names
            for i in range (n_materials):
                materials.append([file.readline().strip()])
            #material properties
            for i in range (n_materials):
                file.readline(); # TODO: name checking
                for n in range(4):
                    s1=file.readline()
                    v1=s1.split()
                    print("Reading material component,n=",n,"  comp=",v1)
                    if (n==2)and(len(v1)==5): #Specular,5 components
                        materials[i].append([float(v1[0]),float(v1[1]),float(v1[2]),float(v1[3]),float(v1[4])])
                    else:   #Other, 4 components
                        materials[i].append([float(v1[0]),float(v1[1]),float(v1[2]),float(v1[3])])
        #---------------Reading TEXTURES section------------------
        elif v[0]=="TEXTURES":
            n_textures=int(v[1]);
            for i in range(n_textures):
                textures.append([file.readline().strip(),"ORBTexture"+str(i)])
       

   
    print("");
    print("==========================Summary===========================================")
    print("Headers: groups=",n_groups," materials=",n_materials," textures=",n_textures)
    print("\nData:\nGroups:")
    print(groups,"\nReal No=",len(groups))
    print("Materials:",materials) 
    print("Textures:",textures)
    print("Materials in groups:",mat)
    print("Textures in groups:",tex)
    #file 
    file.close()
    create_materials(groups,materials,textures,orbiterpath)
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
    orbiterpath= StringProperty(name="Orbiter Path", description="Orbiter spacesim path", maxlen=1024, default="/home/vlad/programs/orbiter", subtype="DIR_PATH")
    
    convert_coords= BoolProperty(name="Convert coordinates", description="Convert coordinates between left-handed and right-handed systems ('yes' highly recomended)", default=True)


    def execute(self,context):
        print("execute")
        load_msh(self.filepath,self.orbiterpath,self.convert_coords)
        return{"FINISHED"}

    def invoke(self,context,event):
        print("invoke")
        wm=context.window_manager
        wm.add_fileselect(self)
        return {"RUNNING_MODAL"}

def menu_function(self,context):
    self.layout.operator(IMPORT_OT_msh.bl_idname, text="Orbiter Mesh (.msh)")
    

def register():
    print("registering...")
    bpy.types.INFO_MT_file_import.append(menu_function)
 
def unregister():
    print("unregistering...")
    bpy.types.INFO_MT_file_import.remove(menu_function)
 
if __name__ == "__main__":
    register()

