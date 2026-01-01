# This utility fixes broken pythonista files
# by cut and pasting them into new file
import os
import editor
import clipboard
import console
import dialogs
import glob
import pathlib

def clipboard_transfer_replace():
    # 1. Select the file    
    current_dir = pathlib.Path.cwd() 
    # go up chain to get to Documents
    while current_dir.name != 'Documents':
        current_dir = current_dir.parent
    os.chdir(current_dir)
    # 2. Define your folder and file names
    folder_name = "Pythonista_games"   

    files = sorted(glob.glob('*/*.py', root_dir='Pythonista_games'), key=str.lower)
    file_name = dialogs.list_dialog('pick file', files)
    
    if not file_name:
        print("Selection cancelled.")
        return
    file_path = current_dir / folder_name / file_name
    temp_path = current_dir / folder_name/ "temp_from_clipboard.py"
    
    try:
        # 2. Read original file and copy to clipboard
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        clipboard.set(content)

        # 3. Paste from clipboard into the temporary file
        # (We retrieve it from the clipboard buffer)
        clipboard_content = clipboard.get()
        
        with open(temp_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(clipboard_content)
        
        # 4. Delete the original file
        os.remove(file_path)
        
        # 5. Rename temporary to original
        os.rename(temp_path, file_path)
        
        console.hud_alert(f'{file_path.name} refreshed!', 'success')
        #print(f"File '{base_name}' has been refreshed via clipboard.")
        print(file_path)
        # Test if now ok by opening
        editor.open_file(str(file_path), new_tab=True)

    except Exception as e:
        console.alert("Error", str(e))

if __name__ == '__main__':
    clipboard_transfer_replace()
