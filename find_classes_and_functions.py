import os
import re

def find_classes_and_functions(root_dir):
    pattern_class = re.compile(r'class (\w+)')
    pattern_func = re.compile(r'def (\w+)')

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(subdir, file), 'r') as f:
                    current_class = None
                    for line in f:
                        match_class = pattern_class.search(line)
                        if match_class:
                            current_class = match_class.group(1)
                        
                        match_func = pattern_func.search(line)
                        if match_func:
                            func = match_func.group(1)
                            print(f"{current_class or 'NoClass'}::{func}")

find_classes_and_functions(".")
