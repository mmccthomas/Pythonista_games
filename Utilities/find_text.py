import os
import console # For Pythonista-specific console output
from glob import glob
# search all of my python files for half remembered methods

search_path = os.path.expanduser('~/Documents')

def search_text_in_modules(search_term, module_names):
    """
    Searches for a given text string within a list of Python modules.

    Args:
        search_term (str): The text string to search for.
        module_names (list): A list of module names (e.g., ['my_module', 'utils']) or iterator
                              These should be relative to the Pythonista script directory
                              or a full path if outside.
    """
    
    print(f"Searching for '{search_term}' in {search_path}")    
    found_any = False

    for module_name in module_names:
        # Construct the full path to the module.
        # In Pythonista, scripts are usually in the 'Documents' directory.
        # You might need to adjust this path if your modules are in subfolders.
        file_path = os.path.join(search_path, f"{module_name}")

        if not os.path.exists(file_path):
            print(f"Warning: Module '{module_name}' not found at {file_path}")   
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                module_found = False
                for line_num, line in enumerate(lines, start=1):
                    if search_term in line:
                        if not module_found:                       
                            print(f"\n--- Found in {module_name} ---")
                            module_found = True
                            found_any = True
                        print(f"  Line {line_num}: {line.strip()}")
        except Exception as e:            
            print(f"Error reading {module_name}: {e}")

    if not found_any:
        print("\nNo occurrences found.")
        console.set_color() # Reset color
    print("\nSearch complete.")

# --- How to use this program in Pythonista ---

if __name__ == '__main__':
    # 1. Define the text you want to search for
    console.clear()
    text_to_find = console.input_alert("Search Text", "Enter the text to search for:", "")
    if not text_to_find:
        print("No search text entered. Exiting.")
    else:       
        print("\nScanning for .py files in your Documents directory...")
        all_py_files = glob('**/*.py', root_dir=search_path,recursive=True)

        if not all_py_files:
            print("No Python files found in your Documents directory.")
            print("No modules specified or found to search. Exiting.")
        else:
            print(f"Found {len(all_py_files)} Python files. Searching all.")
            search_text_in_modules(text_to_find, all_py_files)

        
            

