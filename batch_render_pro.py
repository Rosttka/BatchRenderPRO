bl_info = {
    "name": "Batch Render PRO",
    "author": "Rosttka",
    "version": (1,0,0), 
    "blender": (4, 2, 0),
    "location": "Render Properties > Batch Render Setup",
    "description": "Powerful and stable addon for batch rendering multiple animation actions for different armatures in Blender, ensuring consistent assignments and offering folder management, previewing, and viewport playback. Glory to Ukraine!",
    "category": "Render"
}

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy.types import PropertyGroup, Operator, Panel

# === Property Groups ===
class RenderActionEntry(PropertyGroup):
    # Змінюємо EnumProperty на PointerProperty для стабільності
    object: PointerProperty(type=bpy.types.Object, name="Armature")
    action: PointerProperty(type=bpy.types.Action, name="Action")

class RenderSceneEntry(PropertyGroup):
    folded: BoolProperty(name="Folded", default=False)
    name: StringProperty(name="Scene Name", default="RenderScene")
    active: BoolProperty(name="Active", default=True)
    actions: CollectionProperty(type=RenderActionEntry)
    frame_start: IntProperty(name="Start Frame", default=1)
    frame_end: IntProperty(name="End Frame", default=250)
    output_path: StringProperty(name="Output Path", subtype='DIR_PATH', default="")
    preview_frame: IntProperty(name="Preview Frame", default=1)

class RenderPreviewSettings(PropertyGroup):
    is_rendering: BoolProperty(name="Rendering", default=False)

class RenderFolderEntry(PropertyGroup):
    folder_name: StringProperty(name="Folder Name", default="New Folder")
    active: BoolProperty(name="Active", default=True)
    folded: BoolProperty(name="Folded", default=False)
    render_scenes: CollectionProperty(type=RenderSceneEntry)

# === UI Panel ===
class RENDER_PT_BatchRenderPanel(Panel):
    bl_category = 'Batch Render'
    bl_label = "Batch Render PRO"
    bl_idname = "RENDER_PT_batch_render_panel_safe"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        
        row = layout.row()
        row.operator("render_scene.add_folder", icon="ADD")
        
        for f_index, folder in enumerate(scn.render_folders):
            folder_box = layout.box()
            row = folder_box.row()
            icon = 'TRIA_DOWN' if not folder.folded else 'TRIA_RIGHT'
            toggle = row.operator("render_scene.folder_toggle_fold", text="", icon=icon, emboss=False)
            toggle.folder_index = f_index
            row.prop(folder, "folder_name", text="")
            row.prop(folder, "active", text="Active")
            rem_folder = row.operator("render_scene.remove_folder", text="", icon="X")
            rem_folder.folder_index = f_index
            
            if not folder.folded:
                folder_box.operator("render_scene.add_scene_to_folder", text="Add Scene").folder_index = f_index
                
                for s_index, scene in enumerate(folder.render_scenes):
                    scene_box = folder_box.box()
                    row = scene_box.row()
                    icon_scene = 'TRIA_DOWN' if not scene.folded else 'TRIA_RIGHT'
                    toggle_scene = row.operator("render_scene.toggle_fold", text="", icon=icon_scene, emboss=False)
                    toggle_scene.folder_index = f_index
                    toggle_scene.scene_index = s_index
                    row.prop(scene, "active", text="")
                    row.prop(scene, "name", text="")
                    rem_scene = row.operator("render_scene.remove_scene_from_folder", text="", icon="X")
                    rem_scene.folder_index = f_index
                    rem_scene.scene_index = s_index
                    
                    if not scene.folded:
                        for a_index, act_entry in enumerate(scene.actions): # Змінено 'act' на 'act_entry' для ясності
                            act_box = scene_box.box()
                            row_act = act_box.row()
                            # Використовуємо act_entry.object та act_entry.action для відображення
                            row_act.prop(act_entry, "object", text="Armature") # Змінено текст
                            row_act.prop(act_entry, "action", text="Action")
                            rem_act = row_act.operator("render_scene.remove_action", text="", icon="X")
                            rem_act.folder_index = f_index
                            rem_act.scene_index = s_index
                            rem_act.action_index = a_index
                        add_act = scene_box.operator("render_scene.add_action", text="Add Action")
                        add_act.folder_index = f_index
                        add_act.scene_index = s_index
                        
                        scene_box.prop(scene, "frame_start")
                        scene_box.prop(scene, "frame_end")
                        scene_box.prop(scene, "output_path")
                        
                        row_buttons = scene_box.row(align=True)
                        render_this = row_buttons.operator("render_scene.render_this", text="Render This Frame", icon="RENDER_STILL")
                        render_this.folder_index = f_index
                        render_this.scene_index = s_index
                        row_buttons.prop(scene, "preview_frame", text="Preview Frame")
                        
                        row_play = scene_box.row(align=True)
                        play_vp = row_play.operator("render_scene.play_viewport", text="Play in Viewport", icon="PLAY")
                        play_vp.folder_index = f_index
                        play_vp.scene_index = s_index
                        
            layout.separator(factor=2.0)
        
        row = layout.row()
        row.alert = scn.render_preview_settings.is_rendering
        row.scale_y = 2.0
        row.operator("render_scene.render_all", text="Render Active Scenes", icon="ERROR" if scn.render_preview_settings.is_rendering else "RENDER_ANIMATION")

# === Operators для управління папками ===
class RENDER_OT_AddFolder(Operator):
    bl_idname = "render_scene.add_folder"
    bl_label = "Add Folder"
    
    def execute(self, context):
        folder = context.scene.render_folders.add()
        folder.folder_name = f"Folder_{len(context.scene.render_folders)}"
        return {'FINISHED'}

class RENDER_OT_RemoveFolder(Operator):
    bl_idname = "render_scene.remove_folder"
    bl_label = "Remove Folder"
    
    folder_index: IntProperty()
    
    def execute(self, context):
        context.scene.render_folders.remove(self.folder_index)
        return {'FINISHED'}

class RENDER_OT_FolderToggleFold(Operator):
    bl_idname = "render_scene.folder_toggle_fold"
    bl_label = "Toggle Folder"
    
    folder_index: IntProperty()
    
    def execute(self, context):
        folder = context.scene.render_folders[self.folder_index]
        folder.folded = not folder.folded
        return {'FINISHED'}

# === Operators для управління сценами у папках ===
class RENDER_OT_AddSceneToFolder(Operator):
    bl_idname = "render_scene.add_scene_to_folder"
    bl_label = "Add Scene to Folder"
    
    folder_index: IntProperty()
    
    def execute(self, context):
        folder = context.scene.render_folders[self.folder_index]
        scene = folder.render_scenes.add()
        scene.name = f"RenderScene_{len(folder.render_scenes)}"
        scene.active = True
        return {'FINISHED'}

class RENDER_OT_RemoveSceneFromFolder(Operator):
    bl_idname = "render_scene.remove_scene_from_folder"
    bl_label = "Remove Scene from Folder"
    
    folder_index: IntProperty()
    scene_index: IntProperty()
    
    def execute(self, context):
        folder = context.scene.render_folders[self.folder_index]
        folder.render_scenes.remove(self.scene_index)
        return {'FINISHED'}

# === Operators для управління екшенами в сцені ===
class RENDER_OT_AddActionToScene(Operator):
    bl_idname = "render_scene.add_action"
    bl_label = "Add Action to Scene"
    
    folder_index: IntProperty()
    scene_index: IntProperty()
    
    def execute(self, context):
        folder = context.scene.render_folders[self.folder_index]
        scene_entry = folder.render_scenes[self.scene_index]
        scene_entry.actions.add()
        return {'FINISHED'}

class RENDER_OT_RemoveActionFromScene(Operator):
    bl_idname = "render_scene.remove_action"
    bl_label = "Remove Action from Scene"
    
    folder_index: IntProperty()
    scene_index: IntProperty()
    action_index: IntProperty()
    
    def execute(self, context):
        folder = context.scene.render_folders[self.folder_index]
        scene_entry = folder.render_scenes[self.scene_index]
        scene_entry.actions.remove(self.action_index)
        return {'FINISHED'}

# === Тогл згортання для сцени (всередині папки) ===
class RENDER_OT_ToggleFold(Operator):
    bl_idname = "render_scene.toggle_fold"
    bl_label = "Toggle Fold"
    
    folder_index: IntProperty()
    scene_index: IntProperty()
    
    def execute(self, context):
        folder = context.scene.render_folders[self.folder_index]
        entry = folder.render_scenes[self.scene_index]
        entry.folded = not entry.folded
        return {'FINISHED'}

# === Operators для рендерингу ===
class RENDER_OT_RenderAll(Operator):
    bl_idname = "render_scene.render_all"
    bl_label = "Render Active Scenes"
    
    def execute(self, context):
        scn = context.scene
        scn.render_preview_settings.is_rendering = True
        orig_path = scn.render.filepath
        
        for folder in scn.render_folders:
            if not folder.active:
                continue
            for entry in folder.render_scenes:
                if not entry.active:
                    continue
                # Замість .object_name та .action_name, використовуємо прямі посилання .object та .action
                for act_entry in entry.actions:
                    obj = act_entry.object
                    action = act_entry.action
                    if obj and action:
                        obj.animation_data_create()
                        obj.animation_data.action = action
                
                scn.frame_start = entry.frame_start
                scn.frame_end = entry.frame_end
                scn.render.filepath = bpy.path.abspath(entry.output_path + folder.folder_name + "_" + entry.name)
                scn.render.use_file_extension = True
                
                bpy.ops.render.render('EXEC_DEFAULT', animation=True)
        
        scn.render.filepath = orig_path
        scn.render_preview_settings.is_rendering = False
        return {'FINISHED'}

class RENDER_OT_RenderThisScene(Operator):
    bl_idname = "render_scene.render_this"
    bl_label = "Render This Scene"
    
    folder_index: IntProperty()
    scene_index: IntProperty()
    
    def execute(self, context):
        scn = context.scene
        folder = scn.render_folders[self.folder_index]
        entry = folder.render_scenes[self.scene_index]
        frame = entry.preview_frame
        scn.frame_set(frame)
        # Замість .object_name та .action_name, використовуємо прямі посилання .object та .action
        for act_entry in entry.actions:
            obj = act_entry.object
            action = act_entry.action
            if obj and action:
                obj.animation_data_create()
                obj.animation_data.action = action
        bpy.ops.render.render('INVOKE_DEFAULT')
        return {'FINISHED'}

# === Оновлений оператор Play in Viewport ===
class RENDER_OT_PlayViewport(Operator):
    bl_idname = "render_scene.play_viewport"
    bl_label = "Play in Viewport"
    
    folder_index: IntProperty()
    scene_index: IntProperty()
    
    def invoke(self, context, event):
        return self.execute(context)
    
    def execute(self, context):
        scn = context.scene
        folder = scn.render_folders[self.folder_index]
        entry = folder.render_scenes[self.scene_index]
        
        # Призначення екшенів арматурам для цієї сцени
        for act_entry in entry.actions:
            obj = act_entry.object
            action = act_entry.action
            if obj and action:
                obj.animation_data_create()
                obj.animation_data.action = action
        
        scn.frame_start = entry.frame_start
        scn.frame_end = entry.frame_end
        scn.frame_set(entry.preview_frame)
        bpy.ops.screen.animation_play('INVOKE_DEFAULT')
        return {'FINISHED'}

# === Registration ===
classes = (
    RenderActionEntry,
    RenderSceneEntry,
    RenderPreviewSettings,
    RenderFolderEntry,
    RENDER_PT_BatchRenderPanel,
    RENDER_OT_AddFolder,
    RENDER_OT_RemoveFolder,
    RENDER_OT_FolderToggleFold,
    RENDER_OT_AddSceneToFolder,
    RENDER_OT_RemoveSceneFromFolder,
    # RENDER_OT_MoveSceneUpInFolder, # Ці оператори більше не потрібні, якщо порядок автоматично не змінюється
    # RENDER_OT_MoveSceneDownInFolder, # Ці оператори більше не потрібні
    RENDER_OT_AddActionToScene,
    RENDER_OT_RemoveActionFromScene,
    RENDER_OT_ToggleFold,
    RENDER_OT_RenderAll,
    RENDER_OT_RenderThisScene,
    RENDER_OT_PlayViewport,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_folders = CollectionProperty(type=RenderFolderEntry)
    bpy.types.Scene.render_preview_settings = PointerProperty(type=RenderPreviewSettings)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.render_folders
    del bpy.types.Scene.render_preview_settings

if __name__ == "__main__":
    register()