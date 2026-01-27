import os
import re

def parse_logs(log_files):
    """
    Parses the identified log files and extracts key information for the LLM.
    Returns a string containing the grouped evidence.
    """
    evidence = []
    
    # 1. Parse ANR Files
    if log_files.get("anr_files"):
        evidence.append("=== ANR TRACES ===")
        for anr_file in log_files["anr_files"]:
            try:
                with open(anr_file, 'r', errors='ignore') as f:
                    content = f.read()
                    # Extract the first few lines which usually contain the subject
                    lines = content.splitlines()[:20]
                    subject_line = next((l for l in lines if "Subject:" in l), None)
                    
                    if subject_line:
                        evidence.append(f"File: {os.path.basename(anr_file)}")
                        evidence.append(f"Header: {subject_line}")
                        
                        # Extract Stack Trace for the blocked thread if possible
                        # Simple heuristic: find "blocked" keyword or the thread mentioned in subject
                        target_thread = None
                        match = re.search(r'\((.*?)\)', subject_line)
                        if match:
                            target_thread = match.group(1)
                            
                        if target_thread:
                            # Simple extraction: Find "thread_name" and take next 30 lines
                            # In a real app, we'd need a robust parser
                            idx = content.find(f'"{target_thread}"')
                            if idx != -1:
                                trace_snippet = content[idx:idx+2000] # Cap at 2000 chars
                                evidence.append("Stack Trace Snippet:")
                                evidence.append(trace_snippet)
                                evidence.append("-" * 20)
            except Exception as e:
                print(f"Error parsing ANR {anr_file}: {e}")

    # 2. Parse Main Bugreport
    if log_files.get("bugreport"):
        evidence.append("\n=== SYSTEM LOGS (Relevant Sections) ===")
        try:
            with open(log_files["bugreport"], 'r', errors='ignore') as f:
                # Reading huge files is slow, let's look for specific error patterns
                # For this MVP, we will tail the file and look for strict errors
                # or read the whole thing if < 50MB (bugreports are huge though)
                
                # Strategy: Search for "FATAL EXCEPTION", "Watchdog", "ANR in"
                # We will read line by line
                
                interesting_lines = []
                capture_context = 0
                
                for line in f:
                    if capture_context > 0:
                        interesting_lines.append(line.strip())
                        capture_context -= 1
                        continue
                        
                    if "FATAL EXCEPTION" in line or "ANR in" in line or "Watchdog" in line or "timed out" in line or "timeout" in line or "qcError" in line:
                         interesting_lines.append(f"... {line.strip()}")
                         capture_context = 10 # Capture 10 lines after
                    
                    # Also captures Kernel Panics / OOPS
                    if "Unable to handle kernel paging request" in line:
                         interesting_lines.append(f"KERNEL PANIC: {line.strip()}")
                         capture_context = 20

                # If retrieved lines > 100, just take the last 100 to save tokens
                if len(interesting_lines) > 100:
                    evidence.append("... (earlier logs truncated) ...")
                    evidence.extend(interesting_lines[-100:])
                else:
                    evidence.extend(interesting_lines)
                    
        except Exception as e:
             evidence.append(f"Error reading bugreport: {e}")
             
    display_text = "\n".join(evidence)
    return display_text
