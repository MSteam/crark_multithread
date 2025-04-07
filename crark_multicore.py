#!/usr/bin/env python3
import os
import subprocess
import threading
import time
import itertools
import sys

# =======================
# Configuration Settings
# =======================
max_instances = 36

# Launch parameters:
min_len = 6
max_len = 6
archive_filename = "Addon.rar"

# Charset and combination settings.
charset = "abcdefghijklmnopqrstuvwxyz0123456789"
combination_length = 2

save_filename = "save_progress.txt"

# =====================
# Resume from save file
# =====================
start_index = 0
if os.path.exists(save_filename):
    answer = input(f"A save file '{save_filename}' was found. Do you want to resume from saved progress? (Y/N): ").strip().lower()
    if answer == 'y':
        try:
            with open(save_filename, "r") as f:
                saved_value = f.read().strip()
                if saved_value.isdigit():
                    start_index = int(saved_value)
                    print(f"Resuming from combination index {start_index}.")
                else:
                    print("Save file content invalid. Starting from beginning.")
        except Exception as e:
            print("Error reading save file, starting from beginning:", e)
    else:
        os.remove(save_filename)
        print("Save file removed. Starting from beginning.")

# ======================
# Generate Combinations
# ======================
combinations = [''.join(t) for t in itertools.product(charset, repeat=combination_length)]
total = len(combinations)

# ======================
# Global Variables
# ======================
processes = []       # List of currently running processes.
threads = []         # Monitoring threads for each process.
process_files = {}   # Mapping: process -> associated .def filename.
found_crc_event = threading.Event()  # Set when any process outputs "CRC OK".
save_requested = threading.Event()     # Set when user requests to save progress.
crc_line = None
crc_line_lock = threading.Lock()

# ============================
# Process Output Monitor
# ============================
def monitor_process(proc, identifier):
    global crc_line
    for line in iter(proc.stdout.readline, ''):
        line = line.strip()
        if "CRC OK" in line:
            with crc_line_lock:
                if not found_crc_event.is_set():
                    crc_line = line
                    found_crc_event.set()
            break
    proc.stdout.close()

# ============================
# Launch a Process Instance
# ============================
def launch_instance(combo):
    filename = f"{combo}.def"
    with open(filename, "w") as file:
        file.write(f"##\n{combo}[$a $1] *")
    print(f"Created file: {os.path.abspath(filename)}")

    # Build command using the launch parameters.
    cmd = ["crark", f"-p{filename}", f"-l{min_len}", f"-g{max_len}", archive_filename]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True
    )
    processes.append(proc)
    process_files[proc] = filename

    t = threading.Thread(target=monitor_process, args=(proc, filename), daemon=True)
    t.start()
    threads.append(t)

    print(f"Launched: {' '.join(cmd)}")

# ===============================
# Keyboard Monitor for Save Input
# ===============================
def keyboard_monitor():
    while True:
        if found_crc_event.is_set():
            break
        inp = input("Press 's' (and Enter) at any time to save progress and exit: ").strip().lower()
        if inp == 's':
            save_requested.set()
            print("Save requested. Waiting for running processes to finish...")
            break

kb_thread = threading.Thread(target=keyboard_monitor, daemon=True)
kb_thread.start()

# =========================
# Main Process Launch Loop
# =========================
index = start_index
while index < total and len(processes) < max_instances and not save_requested.is_set():
    launch_instance(combinations[index])
    index += 1

while not found_crc_event.is_set() and not save_requested.is_set():
    for proc in processes.copy():
        if proc.poll() is not None:  # Process has finished.
            processes.remove(proc)
            filename = process_files.pop(proc, None)
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"Deleted file: {filename}")
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
            if index < total and not save_requested.is_set():
                launch_instance(combinations[index])
                index += 1
    if index >= total and not processes:
        break
    time.sleep(0.1)

# =============================
# Save Requested: Finish & Save
# =============================
if save_requested.is_set() and not found_crc_event.is_set():
    while processes:
        for proc in processes.copy():
            if proc.poll() is not None:
                processes.remove(proc)
                filename = process_files.pop(proc, None)
                if filename and os.path.exists(filename):
                    try:
                        os.remove(filename)
                        print(f"Deleted file: {filename}")
                    except Exception as e:
                        print(f"Error deleting file {filename}: {e}")
        time.sleep(0.1)
    with open(save_filename, "w") as f:
        f.write(str(index))
    print(f"Progress saved at combination index {index}. Exiting.")
    os._exit(0)

# ================================
# CRC OK Found: Terminate Instances
# ================================
if found_crc_event.is_set():
    for proc in processes:
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

time.sleep(0.5)
for proc in processes:
    try:
        proc.wait(timeout=1)
    except Exception:
        pass

for proc, filename in list(process_files.items()):
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"Deleted file: {filename}")
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
    process_files.pop(proc, None)

for t in threads:
    t.join()

# Create pass file if "CRC OK" was found.
if found_crc_event.is_set() and crc_line is not None:
    pass_filename = f"pass_{archive_filename}.txt"
    try:
        with open(pass_filename, "w") as f:
            f.write(crc_line)
        print(f"Pass file created: {pass_filename}")
    except Exception as e:
        print(f"Error creating pass file: {e}")

if crc_line is not None:
    print("Found line:", crc_line)
else:
    print("Finished processing all combinations without finding 'CRC OK'.")

os._exit(0)
