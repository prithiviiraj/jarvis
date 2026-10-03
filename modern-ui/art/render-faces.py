import bpy,math,pathlib,json,sys
from mathutils import Vector
out=pathlib.Path(sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else '/tmp/jarvis-art/frames');out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.world.color=(.22,.22,.22)
scene.view_settings.view_transform='AgX'
def mat(name,color,metal=0,rough=.38):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
skin=mat('ceramic',(.16,.65,.51),.18,.28);white=mat('warm eye ivory',(.93,.91,.83),.05,.23);dark=mat('graphite',(.026,.032,.046),.1,.25);iris=mat('iris',(.025,.14,.16),.4,.23);shine=mat('shine',(1,1,1),0,.1);blush=mat('soft blush',(.61,.26,.28),0,.4);accent=mat('edge',(.65,.93,.86),.5,.2)
parts=[]
def sphere(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);bpy.ops.object.shade_smooth();parts.append(o);return o
def tube(name,points,r,material):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=24;c.bevel_depth=r;c.bevel_resolution=5;s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for p,co in zip(s.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(material);parts.append(o);return o
head=sphere('head',(0,0,0),(.90,.70,.98),skin)
# Distinct stylized ceramic heads, actual mesh geometry, soft studio lighting.
ears=[sphere('ear',(x,0,.04),(.18,.22,.29),skin) for x in (-.88,.88)]
for x in (-.40,.40):
 sphere('eye white',(x,-.604,.25),(.255,.14,.285),white)
 sphere('iris',(x,-.741,.25),(.117,.045,.151),iris)
 sphere('pupil',(x,-.784,.25),(.063,.025,.087),dark)
 sphere('glint',(x-.026,-.813,.308),(.028,.014,.032),shine)
 sphere('cheek',(x*1.28,-.557,-.16),(.145,.034,.07),blush)
nose=sphere('nose',(0,-.695,.02),(.116,.18,.135),skin)
brows=[]
for x in (-.40,.40):brows.append(tube('brow',[(x-.20,-.643,.61),(x,-.73,.67),(x+.20,-.643,.61)],.035,dark))
smile=tube('smile',[(-.30,-.595,-.31),(0,-.711,-.44),(.30,-.595,-.31)],.037,dark)
mouth=sphere('speaking mouth',(0,-.694,-.37),(.18,.035,.09),dark);mouth.hide_render=True
# Small sculpted swept hair strands, not flat painted shapes.
hair=[]
hair.append(sphere('sculpted hair cap',(0,.01,.78),(.84,.64,.27),dark))
for i in range(5):
 x=-.56+i*.23;hair.append(tube('swept lock',[(x-.14,-.45,.70),(x-.02,-.46,.88),(x+.24,-.25,.94)],.074,dark))
root=bpy.data.objects.new('face rig',None);bpy.context.collection.objects.link(root)
for p in parts:p.parent=root
for location,power,size in [((-3,-4,5),550,4),((4,-1,3),420,3),((0,3,3),650,3)]:
 bpy.ops.object.light_add(type='AREA',location=location);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-5.5,.4));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,.02))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=2.70;scene.camera=camera
colors={'JARVIS':(.13,.57,.45),'NOVA':(.42,.25,.65),'KAI':(.83,.39,.14),'LYRA':(.73,.22,.43),'DEX':(.16,.40,.77)}
preview='--preview' in sys.argv
manifest={'version':1,'width':512,'height':512,'format':'png-sequence','personas':{}}
for persona,color in colors.items():
 if '--persona' in sys.argv and persona!=sys.argv[sys.argv.index('--persona')+1]:continue
 skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);manifest['personas'][persona]={}
 for state in ['idle','thinking','speaking']:
  frames=[];count=1 if preview else 12
  for i in range(count):
   eyeSquint=.28 if state=='idle' and i==10 else 1.0
   for o in parts:
    if o.name.startswith('eye white'):o.scale.z=.285*eyeSquint
    if o.name.startswith('iris'):o.scale.z=.151*eyeSquint
    if o.name.startswith('pupil'):o.scale.z=.087*eyeSquint
    if o.name.startswith('glint'):o.hide_render=eyeSquint<1
   phase=2*math.pi*i/12;root.rotation_euler=(math.radians(2)*math.sin(phase),0,math.radians(3)*math.sin(phase));root.location.z=.018*math.sin(phase)
   if state=='thinking':root.rotation_euler.z=math.radians(-10)+math.radians(2)*math.sin(phase)
   smile.hide_render=state=='speaking';mouth.hide_render=state!='speaking';mouth.scale.z=.065+.06*(.5+.5*math.sin(phase*2))
   path=out/persona/state/f'{i:04d}.png';path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append(f'{persona}/{state}/{i:04d}.png')
  manifest['personas'][persona][state]={'fps':12,'frames':frames}
 if preview:break
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'original-faces.blend'))
