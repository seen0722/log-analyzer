import zipfile
import os
import re

def extract_zip_and_find_logs(zip_path, extract_to):
    """
    Extracts the zip file and returns a dictionary with paths to key log files.
    Structure:
    {
        "bugreport": "/path/to/bugreport.txt",
        "anr_files": ["/path/to/anr1", "/path/to/anr2"],
        "logcat": "/path/to/logcat.txt" # optional, if separate
    }
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        
    log_files = {
        "bugreport": None,
        "anr_files": [],
        "other_logs": []
    }
    
    # Walk through the extracted directory
    for root, dirs, files in os.walk(extract_to):
        for file in files:
            full_path = os.path.join(root, file)
            
            # 1. Identify Main Bugreport File
            # Pattern: bugreport-BUILD_ID-DATE.txt
            if file.startswith("bugreport-") and file.endswith(".txt") and "dumpstate_log" not in file:
                log_files["bugreport"] = full_path
                
            # 2. Identify ANR Files
            # Usually in FS/data/anr/
            if "FS/data/anr" in full_path and "trace" in file or file.startswith("anr_"):
                 log_files["anr_files"].append(full_path)
                 
    return log_files
