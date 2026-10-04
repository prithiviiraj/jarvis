"""Original JARVIS soft creature mascots. No Muse model, texture or branding used."""
import bpy,math,pathlib,json,sys
from mathutils import Vector
out=pathlib.Path(sys.argv[sys.argv.index('--out')+1]if '--out'in sys.argv else'/tmp/jarvis-mascots');out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.world.color=(.15,.15,.15);scene.view_settings.view_transform='AgX'
def mat(name,color,rough=.48):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
dark=mat('soft espresso',(.029,.025,.038));cream=mat('warm cream',(.94,.88,.75));light=mat('eye catchlight',(1,1,1),.2);pink=mat('warm cheek',(.92,.44,.49))
parts=[]
def oval(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);bpy.ops.object.shade_smooth();parts.append(o);return o
def curve(name,pts,r,material):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=r;c.bevel_resolution=4;b=c.splines.new('BEZIER');b.bezier_points.add(len(pts)-1)
 for p,co in zip(b.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(material);parts.append(o);return o
for loc,power,size in [((-3,-4,5),500,4),((4,-2,2),300,4),((0,3,4),550,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(Vector((0,0,.1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-6,1.1));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,.12))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=2.85;scene.camera=camera
specs={'JARVIS':((.36,.76,.63),'round'), 'NOVA':((.64,.48,.85),'bunny'),'KAI':((.96,.59,.30),'fox'),'LYRA':((.91,.48,.66),'cat'),'DEX':((.39,.61,.91),'sprout')}
manifest={'version':1,'width':512,'height':512,'format':'png-sequence','design':'Original soft creature mascots','personas':{}}
for persona,(color,kind)in specs.items():
 if '--persona'in sys.argv and persona!=sys.argv[sys.argv.index('--persona')+1]:continue
 parts=[];skin=mat(persona+' soft clay',color);root=bpy.data.objects.new(persona+' animation rig',None);bpy.context.collection.objects.link(root)
 body=oval('plump body',(0,0,-.08),(.78,.56,.84),skin);oval('cream belly',(0,-.491,-.24),(.46,.085,.49),cream)
 for x in (-.49,.49):oval('tiny foot',(x,-.07,-.79),(.22,.30,.14),skin)
 arms=[]
 for x in (-.72,.72):arms.append(oval('tiny paw',(x,-.10,-.19),(.19,.22,.30),skin))
 if kind=='round':
  for x in (-.55,.55):oval('round ear',(x,.015,.68),(.29,.23,.30),skin);oval('ear inner',(x,-.17,.71),(.13,.047,.15),cream)
 elif kind=='bunny':
  for x in (-.34,.34):o=oval('long soft ear',(x,.02,.86),(.19,.19,.49),skin);o.rotation_euler.y=x*.22;oval('ear inner',(x,-.16,.93),(.077,.034,.28),cream)
 elif kind=='fox':
  for x in (-.51,.51):o=oval('fox ear',(x,.01,.70),(.26,.22,.38),skin);o.rotation_euler.y=-x*.5;oval('ear inner',(x,-.19,.76),(.11,.033,.22),cream)
 elif kind=='cat':
  for x in (-.50,.50):o=oval('kitten ear',(x,0,.69),(.24,.23,.29),skin);o.rotation_euler.y=-x*.6
  oval('tail',(.77,.26,-.35),(.21,.19,.44),skin)
 else:
  for x in (-.18,.18):o=oval('sprout tuft',(x,.02,.83),(.14,.18,.28),skin);o.rotation_euler.y=x*1.4
  for x in (-.75,.75):oval('rounded side fin',(x,.03,.25),(.18,.20,.20),skin)
 eyes=[];glints=[]
 for x in (-.25,.25):
  eyes.append(oval('bead eye',(x,-.561,.18),(.095,.053,.135),dark));glints.append(oval('catchlight',(x-.022,-.608,.226),(.022,.013,.026),light));oval('blush',(x*1.68,-.50,-.04),(.103,.027,.047),pink)
 smile=curve('small warm smile',[(-.105,-.576,-.015),(0,-.596,-.071),(.105,-.576,-.015)],.024,dark);mouth=oval('talking mouth',(0,-.578,-.045),(.077,.031,.075),dark);mouth.hide_render=True
 brows=[curve('expressive brow',[(x-.07,-.537,.39),(x,-.562,.42),(x+.07,-.537,.39)],.017,dark)for x in (-.25,.25)]
 for o in parts:o.parent=root
 manifest['personas'][persona]={}
 for state in ('idle','thinking','speaking'):
  frames=[];count=1 if '--preview'in sys.argv else 16
  for i in range(count):
   phase=2*math.pi*i/16;blink=.12 if state=='idle'and i in (12,13)else 1.;root.location.z=.018*math.sin(phase);root.rotation_euler=(math.radians(2)*math.sin(phase),0,math.radians(2)*math.sin(phase))
   if state=='thinking':root.rotation_euler.z=math.radians(-9)+math.radians(2)*math.sin(phase)
   for o in eyes:o.scale.z=.135*blink;o.location.x=(-.25 if o==eyes[0]else .25)+(.02 if state=='thinking'else .012*math.sin(phase))
   for o in glints:o.hide_render=blink<.5
   for n,o in enumerate(arms):o.rotation_euler.y=(.08 if n else-.08)*math.sin(phase)
   smile.hide_render=state=='speaking';mouth.hide_render=state!='speaking';mouth.scale.z=.04+.05*(.5+.5*math.sin(phase*3))
   for o in brows:o.location.z=.025 if state=='thinking'else 0
   path=out/persona/state/f'{i:04d}.png';path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append(f'{persona}/{state}/{i:04d}.png')
  manifest['personas'][persona][state]={'fps':8,'frames':frames}
 for o in parts:bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.objects.remove(root,do_unlink=True)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'original-mascots.blend'))
