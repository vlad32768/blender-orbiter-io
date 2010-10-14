
# Notes on .msh import:
#
# 1. You should import meshes from Orbiter installation. The module will autodedect Orbiter directory and load textures from Orbiter installation.
#    
# 2. The script doesn't import vertex normals. It seems that Blender often recalculates vertex normals, so it's useless to import them.
#
# 3. If there is one material with different textures in .msh file, the script will create a copy of this material for every texture.
#
# 4. There are no ambient and emissive colors in Blender, so the script doesn't import ambient colors but calculates emit component
#
# 5. Some models (for example DGIV and DG-XR) have got materials with shiny specular and zero hardness. That doesn't look good in blender. 
#    You can use "Raise small hardness" parameter in file import dialog to set minimal hardness manually
#
# 6. Blender uses right-handed coordinate system, Orbiter uses left-handed one. Also, Blender and Orbiter use different UV coord origins
#  So, the module converts vertex and UV coordinates 
#  Conversion from orbiter coordinate system is: 
#  1. Coordinate system conversion:z=y ; y=-z; x=-x
#  2. Triangle backface flipping: tri[1]<->tri[2]
#  3. UV coord system conversion: v=1-v
#  So, conversion to orbiter is: z=-y,y=z,x=-x ; tri[1]<-> tri[2] ; v=1-v

# Notes on .msh export
#
# 1. Coordinate system: The script does conversion to left handed coordinate system, so there is the proper way to place your model in Blender when you start modeling:
#    -- Y axis is the main thrust direction;
#    -- Z axis points UP;
#    -- X axis points LEFT.
# 2. Materials: 
#    -- The script makes Ambient color equal to Diffuse;
#    -- Emissive color is equal to Diffuse*emit
# 3. Textures
#    -- If you export your model to "file.msh", textures will be saved in "filetex" directory near the .msh file.
#       "file.msh" should be copied to Orbiter's "Meshes" directory, "filetex" directory -- to "Textures" (see TEXTURES section of .msh file)
#    -- Blender does not support writing .DDS files. In most cases the script will save .png files (check it). 
#       So you have to convert textures to .dds manually. However, the script writes names with .dds extension in .msh TEXTURES section 

ORBITER_PATH_DEFAULT="f:\\fs\\orbiter2010" #If module can't autodetect Orbiter installation, it will use this path
#ORBITER_PATH_DEFAULT="/home/vlad/programs/orbiter"

VERBOSE_OUT = False;

bl_addon_info = {
    "name": "Import/Export Orbiter mesh (.msh)",
    "author": "vlad32768",
    "version": (1,0),
    "blender": (2, 5, 4),
    "api": 32391,
    "category": "Import/Export",
    "location": "File > Import > Orbiter mesh (.msh); File > Export > Orbiter mesh (.msh)",
    "warning": 'Beta 1 version', # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/My_Script",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=#&group_id=#&atid=#",
    "description": """\
Imports and exports Orbiter mesh file (as well as materials and textures).
"""}


import bpy

import io #file i/o
import os
import ntpath

####################################################
## IMPORT PART
####################################################
def create_mesh(name,verts,faces,norm,uv,param_vector):
    '''Function that creates mesh from loaded data'''

    show_single_sided=param_vector[1]

    me = bpy.data.meshes.new(name+"Mesh")
    ob = bpy.data.objects.new(name, me)
    ob.location =(0,0,0) #origin
    # Link object to scene
    bpy.context.scene.objects.link(ob)
    if show_single_sided:
        me.show_double_sided=False
    # from_pydata doesn't work correctly, it swaps vertices in some triangles 
    #me.from_pydata(verts,[], faces)
    me.vertices.add(len(verts))
    me.faces.add(len(faces))
    #me.vertices.foreach_set("co", verts)
    #me.faces.foreach_set("vertices_raw", unpackList(faces))
    for i in range(len(verts)):
        me.vertices[i].co=verts[i]
    for i in range(len(faces)):
        me.faces[i].vertices=faces[i]
    
    #there is something wrong with normals in Blender 
    #if (norm!=[]):
    #    for i in range(len(norm)):
    #        me.vertices[i].normal=norm[i]
    #        print (me.vertices[i].normal)

    if uv!=[]:
        #Loading UV tex coords
        uvtex=me.uv_textures.new()#create uvset
        for i in range(len(faces)):
            uvtex.data[i].uv1=uv[faces[i][0]]
            uvtex.data[i].uv2=uv[faces[i][1]]
            uvtex.data[i].uv3=uv[faces[i][2]]

    # Update mesh with new data
    me.update(calc_edges=True)
    return ob

def join_case_insensitive(fpath,f):
    '''
    helper for find_texture_path()
    Trying to join filepath case-insensitive in Posix systems

    Returns:    joined path if it finds f
                "" if it finds nothing
    ''' 
    ld=os.listdir(fpath)
    if f in set(ld): #the names are equal
        print("Original name is good: ",f)
        return os.path.join(fpath,f)
    else:   # case insensitive search in fpath directory
        for f1 in ld:
            if f.lower()==f1.lower():
                print("modified name is good: ",f,"->",f1)
                return os.path.join(fpath,f1)
        print ("Cannot find '",f,"' file in ",fpath)
        return ""

def find_texture_path(orbiterpath,tex_string):
    '''
    Finds texture file in texture directories
    
    Returns the full texture file path if it exists
    "" if doesn't
    '''
    #perform full split
    v=[]
    tempstr=tex_string
    while True:
        v1=ntpath.split(tempstr)
        v.insert(0,v1[1])
        #print (v1)
        tempstr=v1[0]
        if tempstr=="":
            break
    print(v);
    for texdir in ("Textures","Textures2"):
        fpath=os.path.join(orbiterpath,texdir)
        if not(os.access(fpath,os.F_OK)):
            print("WARNING! There isn't '",texdir,"' dir in ",orbiterpath)
            return ""
        find_all=True
        for f in v:
            # Handle upper/lwercase POSIX problem, buggy if all 2 tex dirs contains the same subdirs
            if f=="":
                continue #skip empty ntpath.split() members
            temppath=join_case_insensitive(fpath,f)
            if temppath=="":
                find_all=False
                if texdir=="Texture2":
                    print ("Warning! Cannot find '",f,"' file in all 2 directories!")
                    return ""
                else:
                    break #continue with "Textures2" folder
            else:
                fpath=temppath
            # end of upper/lowercase handling
            #fpath=os.path.join(fpath,f) #Construct path without upper/lowercase handling
        if find_all:
            break   # Stop searching
    if os.access(fpath,os.R_OK)and os.path.isfile(fpath):
        print ("File exists and can be read:",fpath)
        return fpath
    else:   # probably this will never run
        print ("Warning! File",tex_string," not exists or cannot be read in:",fpath)
        return ""

def create_materials(groups,materials,textures,orbiterpath,param_vector):
    '''
    To create materials, some steps has to be done:
    1. Create unique material+texture pairs with corresponding mesh groups
    2. Create textures
    3. Create materials,assign textures to them if needed, assign materials to mesh groups
    '''


    #1. ==========counting material/texture combinations===========
    print("-----------Creating materials-----------")
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


    print("\nUnique pairs:",len(matpairset),"\n",matpairset)
    if VERBOSE_OUT:
        print(matpair)
    
    #2.==============create textures=======================
    tx=[]
    tex_load_fails=0
    print ("lalala",orbiterpath)
    orbiter_path_ok=os.access(orbiterpath,os.F_OK)
    if not(orbiter_path_ok):
        print("Orbiter path is wrong! path=",orbiterpath)
    print("creating textures")
    for n in range(len(textures)):
        tx.append(bpy.data.textures.new(textures[n][1],"IMAGE"))
        if orbiter_path_ok:
            fpath=find_texture_path(orbiterpath,textures[n][0])
            if fpath=="":
                tex_load_fails=tex_load_fails+1
                continue 
            #Trying to load data
            try:
                img=bpy.data.images.load(fpath)
            except:
                print("Can not load image, file is possibly corrupted : ",fpath)
                tex_load_fails=tex_load_fails+1
                continue 
        else:
            tex_load_fails=tex_load_fails+1
            continue
        tx[n].image=img
        tx[n].use_alpha=True

    #3.=================Create materials=====================    
    print("creating materials") 
    n=0
    matt=[]
    mat_index_out_of_range=False
    for pair in matpair:
        #create material object
        idx_mat=pair[0][0]-1
        if (idx_mat)>len(materials)-1: #There are some .msh files with wrong mat indices
            mat_index_out_of_range=True
            print("WARNING! Material index out of range in GEOM(s):",pair[1],". Using the last material.")
            idx_mat=len(materials)-1
        idx_tex=pair[0][1]-1
        if VERBOSE_OUT:
            print("idx_mat=",idx_mat)
            print("mat_name=",materials[idx_mat][0])
            print("diff=",materials[idx_mat][1][:3])
            if len(textures)>0:
                print("tex=",textures[idx_tex][1],"idx=",idx_tex)
        matt.append(bpy.data.materials.new(materials[idx_mat][0]))
        #diffuse component
        matt[n].diffuse_color=materials[idx_mat][1][:3]
        matt[n].alpha=materials[idx_mat][1][3]
        if materials[idx_mat][1][3]<1.0:
            matt[n].use_transparency=True
        #specular component
        matt[n].specular_color=materials[idx_mat][3][:3]
        matt[n].specular_alpha=materials[idx_mat][3][3]  
        
        raise_small_hardness=param_vector[2]
        default_hardeness=param_vector[3]
        if len(materials[idx_mat][3])==5:
            if raise_small_hardness and (materials[idx_mat][3][4]<default_hardeness):
                matt[n].specular_hardness=default_hardeness
            else:
                matt[n].specular_hardness=materials[idx_mat][3][4]
        #there aren't different ambient and emissive color component in blender
        #ambient is very often equal to diffuse, it's like amb=1.0 in blender
        #Emmissive component:
        import_emmissive=True;
        if import_emmissive:
            emm_c=materials[idx_mat][4][:3]
            matt[n].emit=(emm_c[0]+emm_c[1]+emm_c[2])/3
        
        #Adding texture to material
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
    print("=============Materials creation summary:=================")
    print("Created ",n," materials,")
    print("Loaded ",len(tx)-tex_load_fails," textures.")
    if not(orbiter_path_ok):
        print("WARNING! Orbiter path is wrong or not accessible, textures cannot be loaded!")
        print("Wrong path=",orbiterpath)

    if tex_load_fails>0:
        print("WARNING! ",tex_load_fails," of ",len(tx)," textures aren't loaded, possibly wrong file name(s)!")

    if mat_index_out_of_range:
        print("WARNNG! Material numbers of some GEOMs are out of range, see above!")

def extract_orbpath_from_filename(fname):
    '''
    Extract Orbiter path from file name
    The function assumes that Orbiter directory is 
    the parent of the first "Meshes" directory.

    It returns path on success; empty string on fail
    '''
    s=fname
    while True:
        v=os.path.split(s)
        s=v[0]
        #print(v)
        if v[1].lower()=="meshes":
            break
        if v[1]=="":#path splitted to root directory, search fails
            s=""
            break;

    if s=='':
        print("WARNING! Orbiter path not found!")
    else:
        print("Orbiter path found: ",s)
    return s
        


#load mesh function
def load_msh(filename,param_vector):
    '''Read MSH file'''

    convert_coords=param_vector[0]

    orbiterpath=ORBITER_PATH_DEFAULT
    s=extract_orbpath_from_filename(filename)
    if s!="":
        orbiterpath=s
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
        if len(v)==0:
            continue # skip empty lines
        #print (v)
        #------Reading GROUPS section-------------
        if v[0]=="GROUPS":
            print("------------------------Reading groups:----------------------------")
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
                    n_mat=int(v1[1].rstrip(";"))  #rstrip is for buggy files with ";" after digit
                if v1[0]=="TEXTURE":
                    n_tex=int(v1[1].rstrip(";"))  

                #Reading geometry
                if v1[0]=="GEOM":
                    vtx=[]
                    tri=[]
                    norm=[]
                    uv=[]
                    
                    nv=int(v1[1])
                    nt=int(v1[2].rstrip(";"))
                    if VERBOSE_OUT:
                        print ("Group No:",n_grp," verts=",nv," tris=",nt)
                    for n in range(nv):
                        s2=file.readline();
                        v2=s2.split();
                        #print(v2);
                        #if label=="cargodooroutL":
                        #    print("#####RAW DATA OF GEOM: ",label)
                        #    print (v2)
                        if convert_coords:
                            vtx.append([-float(v2[0]),-float(v2[2]),float(v2[1])])# convert from left-handed coord system
                        else: 
                            vtx.append([float(v2[0]),float(v2[1]),float(v2[2])]) #without conversion 
                        if len(v2)>5: #there are normals (not vtx+uvs only)
                            #should I convert the normals?
                            norm.append([float(v2[3]),float(v2[4]),float(v2[5])])
                        
                        convert_uvs=True; ##test mode= uvs without conversion
                        if len(v2)==8: #there are normals and uvs
                            if convert_uvs:
                                #in Blender, (0,0) is the upper-left corner. 
                                #in Orbiter -- lower-left corner. So I must invert V axis
                                uv.append([float(v2[6]),1.0-float(v2[7])])    
                            else:
                                uv.append([float(v2[6]),float(v2[7])])
                        elif len(v2)==5: #there are only uvs
                            if convert_uvs:
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
                    obj=create_mesh(label,vtx,tri,norm,uv,param_vector)
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
                file.readline(); # TODO: material name checking
                for n in range(4):
                    s1=file.readline()
                    v1=s1.split()
                    if VERBOSE_OUT:
                        print("Reading material component,n=",n,"  comp=",v1)
                    if (n==2)and(len(v1)==5): #Specular,5 components
                        materials[i].append([float(v1[0]),float(v1[1]),float(v1[2]),float(v1[3]),float(v1[4])])
                    else:   #Other, 4 components
                        materials[i].append([float(v1[0]),float(v1[1]),float(v1[2]),float(v1[3])])
        #---------------Reading TEXTURES section------------------
        elif v[0]=="TEXTURES":
            print("-----------Reading TEXTURES section---------------")
            n_textures=int(v[1]);
            for i in range(n_textures):
                textures.append([file.readline().split()[0],"ORBTexture"+str(i)]) #split to get rid of "D"s
       

   
    print("");
    print("==========================File reading summary====================================")
    print("Headers: groups=",n_groups," materials=",n_materials," textures=",n_textures)
    if VERBOSE_OUT: 
        print("\nData:\n-----------Groups:------------\n",groups)
        print("-----------------Materials:------------\n",materials) 
        print("------------------Textures:------------\n",textures)
    print("\nReal groups No=",len(groups),"; materials:",len(materials),"; textures=",len(textures))
    file.close() #end reading file
    create_materials(groups,materials,textures,orbiterpath,param_vector)
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
    
    #orbiterpath= StringProperty(name="Orbiter Path", description="Orbiter spacesim path", maxlen=1024, default=ORBITER_PATH_DEFAULT, subtype="DIR_PATH")
    
    convert_coords= BoolProperty(name="Convert coordinates", description="Convert coordinates between left-handed and right-handed systems ('yes' highly recomended)", default=True)
    show_single_sided= BoolProperty(name="Show single-sided", description="Disables 'Double Sided' checkbox, some models look better if enabled", default=True)
    raise_small_hardness= BoolProperty(name="Raise small hardness", description="Raise small hardness for some models", default=False)
    default_hardness=IntProperty(name="Hardness",description="Smallest hardness",default=20)

    def execute(self,context):
        print("execute")
        param_vector=[self.convert_coords,self.show_single_sided,self.raise_small_hardness,self.default_hardness]
        load_msh(self.filepath,param_vector)
        return{"FINISHED"}

    def invoke(self,context,event):
        print("invoke")
        wm=context.window_manager
        wm.add_fileselect(self)
        return {"RUNNING_MODAL"}

def import_menu_function(self,context):
    self.layout.operator(IMPORT_OT_msh.bl_idname, text="Orbiter Mesh (.msh)")
############################################################
## END OF IMPORT PART
############################################################

############################################################
## EXPORT PART
############################################################

def export_msh(filepath,convert_coords):
   
    nonormal=False
  
    if os.path.splitext(filepath)[1]=="":
        filepath=filepath+".msh"

    file=open(filepath,"w")
    file.write("MSHX1\n")
    ngroups=0 
    for obj in bpy.context.selected_objects:
        if obj.type=='MESH':
            ngroups=ngroups+1
    file.write("GROUPS {}\n".format(ngroups))
   
    mtrls={}
    txtrs={}

    for obj in bpy.context.selected_objects:
        if obj.type=='MESH':
            matrix=obj.matrix_world
            me=obj.data
            n=0
            vtx=[]
            faces=[]
           
            
            file.write("LABEL {}\n".format(obj.name))
            # Adding materials and textures
            if len(obj.material_slots)!=0:
                mat=obj.material_slots[0].material
                if not (mat.name in mtrls):
                    print("Mew material:",mat.name)
                    mtrls[mat.name]=len(mtrls)
                file.write("MATERIAL {}\n".format(mtrls[mat.name]))

                if mat.texture_slots[0]!=None:
                    tex=mat.texture_slots[0].texture
                    if tex.type=="IMAGE": #Texture type must be image
                        if not(tex.name in txtrs):
                            print("New texture:",tex.name)
                            txtrs[tex.name]=len(txtrs)
                        file.write("TEXTURE {}\n".format(txtrs[tex.name]))
                    else:
                        print("Non-image texture")
                        
            #preparing vertices array: coords and normal
            for vert in me.vertices:
                vtx.append([matrix*vert.co,vert.normal])
            
            has_uv=True;
            if len(me.uv_textures)==0:
                has_uv=False;
                print("Mesh ",obj.name,"has not UV map" )
                
            #Creating faces array and finishing vtx array with UVs
            for n in range(len(me.faces)):
                face=me.faces[n]
                
                if has_uv:# 3 UVs 
                    changeface=False
                    fc=[]#face to add
                    for i in range(len(face.vertices)):
                        uvs=me.uv_textures[0].data[n].uv_raw[(2*i):(2*i+2)]
                        idx_vert=face.vertices[i]
                        if len(vtx[idx_vert])==2: #no UVs yet, add idx_vert  to fc and uvs to vert
                            vtx[idx_vert].append(uvs)
                            fc.append(idx_vert)
                        else:
                            if vtx[idx_vert][2]==uvs:#UVs are equal, just add idx_vert to fc
                                #print("uvs equal")
                                fc.append(idx_vert)
                            else: #uvs differ, add new vtx and use new idx_vert
                                vtx.append([vtx[idx_vert][0],vtx[idx_vert][1],uvs])
                                fc.append(len(vtx)-1)
                    #Add resulting fc
                    faces.append(fc[:3])
                    if len(fc)==4:
                        faces.append([fc[2],fc[3],fc[0]])

                
                else:#export just faces without uv
                    faces.append(face.vertices[:3]) #first (or alone) triangle
                    if len(face.vertices)==4: #2nd triangle if face is quad
                        #print("!!!tetragon!!!")
                        faces.append([face.vertices[2],face.vertices[3],face.vertices[0]])
                    #else:
                    #    print("triangle")
            print("====Mesh Geometry Summary====")
            if VERBOSE_OUT:
                for v in vtx:
                    print(v)
                print("---")
                print(faces)
            print("vtx: ",len(vtx),"  faces:",len(faces))

            #write GEOM section 
            if nonormal:
                file.write("NONORMAL\n")
            file.write("GEOM {} {}\n".format(len(vtx),len(faces)))
            if convert_coords:
                for v in vtx:
                    file.write("{} {} {}".format(-v[0][0],v[0][2],-v[0][1]))
                    if not nonormal: #I think normal coords should be converted too
                        file.write(" {} {} {}".format(-v[1][0],v[1][2],-v[1][1]))
                    if has_uv:
                        file.write(" {} {}".format(v[2][0],1-v[2][1]))        
                    file.write("\n")
                for f in faces:
                    file.write("{} {} {}\n".format(f[0],f[2],f[1]))
            else:
                for v in vtx:
                    file.write("{} {} {}".format(v[0][0],v[0][1],v[0][2]))
                    if not nonormal:
                        file.write(" {} {} {}".format(v[1][0],v[1][1],v[1][2]))
                    if has_uv:
                        file.write(" {} {}".format(v[2][0],1-v[2][1]))        
                    file.write("\n")
                for f in faces:
                    file.write("{} {} {}\n".format(f[0],f[1],f[2]))
    #write other sections
    print("===Materials summary====")
    print(mtrls)
    print("===Textures summary=====")
    print(txtrs)
    #===Write MATERIALS section=====
    file.write("MATERIALS {}\n".format(len(mtrls))) #just mtrls sorted by values
    temp_m=sorted(mtrls.items(),key=lambda x: x[1])
    for m in temp_m:
        file.write("{}\n".format(m[0]))
    
    for m in temp_m:
        file.write("MATERIAL {}\n".format(m[0]))
        
        mat=bpy.data.materials[m[0]]
        dc=mat.diffuse_color
        file.write("{} {} {} {}\n".format(dc[0],dc[1],dc[2],mat.alpha))
        file.write("{} {} {} {}\n".format(dc[0],dc[1],dc[2],mat.alpha))
        sc=mat.specular_color
        file.write("{} {} {} {} {}\n".format(sc[0],sc[1],sc[2],mat.specular_alpha,mat.specular_hardness))
        file.write("{} {} {} {}\n".format(dc[0]*mat.emit,dc[1]*mat.emit,dc[2]*mat.emit,mat.alpha))
    #=====Write TEXTURES section ======
    file.write("TEXTURES {}\n".format(len(txtrs)))
    
    v=os.path.split(filepath)
    mshdir=v[0]
    mshname=os.path.splitext(v[1])[0]
    texdir=mshname+"tex"
    texpath=os.path.join(mshdir,texdir)

    temp_t=sorted(txtrs.items(),key=lambda x: x[1])
    for t in temp_t:
        tex=bpy.data.textures[t[0]]
        img_fp=tex.image.filepath
        
        tex_fname=""

        if img_fp=="Untitled": #new name from tex name
            tex_fname=tex.name+"."+tex.image.file_format.lower()
            tex.image.save_render(os.path.join(texpath,tex_fname))
        else: #image file is already saved on disk
            tex_fname=os.path.split(img_fp)[1]
            if tex.image.file_format=="":#if no format (dds) it will be saved as png.
                tex_fname=os.path.splitext(tex_fname)[0]+".png"
            tex.image.save_render(os.path.join(texpath,tex_fname))
        
        file.write("{}\n".format(ntpath.join(texdir,os.path.splitext(tex_fname)[0]+".dds"))) #local dir + fname+'dds' 

    file.close()                


class EXPORT_OT_msh(bpy.types.Operator):
    '''Export MSH Operator'''
    bl_idname="export_mesh.msh"
    bl_label="Export MSH"
    bl_descriptiom="Export an Orbiter mesh (.msh)"
    
    filepath= StringProperty(name="File Path", description="Filepath of exported MSH file", maxlen=1024, default="")
    convert_coords= BoolProperty(name="Convert coordinates", description="Convert coordinates between right-handed and left-handed systems ('yes' highly recomended)", default=True)
   
    def execute(self,context):
        print("Export execute")
        export_msh(self.filepath,self.convert_coords)
        return {"FINISHED"}

    def invoke(self,context,event):
        print("Export invoke")
        wm=context.window_manager
        wm.add_fileselect(self)
        return {"RUNNING_MODAL"}

def export_menu_function(self,context):
    self.layout.operator(EXPORT_OT_msh.bl_idname,text="Orbiter Mesh (.msh)")
 
###########################################
## END OF EXPORT PART
############################################

############## REGISTER PART#########################3

def register():
    print("registering...")
    bpy.types.INFO_MT_file_import.append(import_menu_function)
    bpy.types.INFO_MT_file_export.append(export_menu_function)
 
def unregister():
    print("unregistering...")
    bpy.types.INFO_MT_file_import.remove(import_menu_function)
    bpy.types.INFO_MT_file_export.remove(export_menu_function)
 
if __name__ == "__main__":
    register()

