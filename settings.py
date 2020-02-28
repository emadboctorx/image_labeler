def setup_toolbar(qt_obj):
    tools = {}
    names = ['Upload photo', 'Save', 'Upload Photo Folder', 'Upload video', 'Draw Rectangle', 'Delete',
             'Reset', 'Settings', 'Help']
    icons = ['upload_photo6.png', 'save3.png', 'upload_folder5.png', 'upload_vid3.png',
             'draw_rectangle3.png', 'delete.png', 'reset4.png', 'settings.png', 'help.png']
    methods = [qt_obj.upload_photo, qt_obj.save_changes, qt_obj.upload_folder, qt_obj.upload_vid,
               qt_obj.draw_rectangle, qt_obj.delete_selected, qt_obj.reset_labels,
               qt_obj.display_settings, qt_obj.display_help]
    tips = ['Upload a photo and add it to the photo list', 'Save changes to disk',
            'Open a folder from the last saved point or open a new one containing '
            'photos and add them to the photo list',
            'Add a video and convert it to .png frames and add them to the photo list',
            'Select a photo and draw a rectangle on the target object(s)',
            'Delete selection', 'Delete all labels in the current working folder',
            'Display settings', 'Display help']
    keys = [f'Ctrl+Shift+{key}' for key in ('OSFVRDJAH')]
    for name, icon, method, tip, key in zip(names, icons, methods, tips, keys):
        tools[name] = name, icon, method, tip, key
    return tools
