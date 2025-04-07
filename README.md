crark_multithread

Python script to launch multiple threads of crark to brute-force RAR password recovery.

This is mostly makes sense for RAR2 archives, as for RAR3 you can use JohnTheReaper to get your password using GPU.

This script creates multiple *.def files with different prefixes that generate from the "charset" variable, defined at the begging of the program.

Contents of the generated definition are written with this line: file.write(f"##\n{combo}[$a $1] *

max_instances = number of cores on your CPU
Launch parameters:

min_len = Minimum password length

max_len = Maximum password length

archive_filename = name of RAR file
Charset and combination settings.

charset = "abcdefghijklmnopqrstuvwxyz0123456789"

combination_length = number of characters generated as prefix for definition file

You can save password search progress when pressing "s" and than "Enter". It will finish all currently running instances and save its progress to "save_progress.txt".

You can continue password recovery at the next program launch.
