def setup_toolbar(qt_obj):
    tools = {}
    names = [
        'Upload photos',
        'Upload Labels',
        'Save',
        'Save Yolo',
        'Save Voc',
        'Upload Photo Folder',
        'Upload video',
        'Edit Mode',
        'Delete Selection(s)',
        'Reset',
        'Settings',
        'Help',
    ]
    icons = [
        'upload_photo6.png',
        'labels.png',
        'save3.png',
        'yolo.png',
        'voc.png',
        'upload_folder5.png',
        'upload_vid3.png',
        'draw_rectangle3.png',
        'delete.png',
        'reset4.png',
        'settings.png',
        'help.png',
    ]
    methods = [
        qt_obj.upload_photos,
        qt_obj.upload_labels,
        qt_obj.save_changes_table,
        qt_obj.save_changes_yolo,
        qt_obj.save_changes_voc,
        qt_obj.upload_folder,
        qt_obj.upload_vid,
        qt_obj.edit_mode,
        qt_obj.delete_selections,
        qt_obj.reset_labels,
        qt_obj.display_settings,
        qt_obj.display_help,
    ]
    keys = 'OLSYPFVRDJAH'
    tips = [
        'Select photos from a folder and add them to the photo list',
        'Upload labels from csv, hdf',
        'Save changes to csv or hdf',
        'Save changes to txt files with Yolo format',
        'Save changes to xml files in Pascal voc format',
        'Open a folder from the last saved point or open a new one containing '
        'photos and add them to the photo list',
        'Add a video and convert it to .png frames and add them to the photo list',
        'Activate editor mode',
        'Delete all selections(checked items)',
        'Delete all labels in the current working folder',
        'Display settings',
        'Display help',
    ]
    tips = [f'Press ⌘⇧{key}:  ' + tip for key, tip in zip(keys, tips)]
    key_shorts = [f'Ctrl+Shift+{key}' for key in keys]
    check_status = [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
    ]
    assert len(names) == len(icons) == len(methods) == len(tips) == len(key_shorts)
    for name, icon, method, tip, key, check in zip(
        names, icons, methods, tips, key_shorts, check_status
    ):
        tools[name] = [name, icon, method, tip, key, check]
    return tools
