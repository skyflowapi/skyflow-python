# import json

# def generate_markdown_from_json(json_file_path):
#     with open(json_file_path, 'r') as f:
#         module_dict = json.load(f)

#     markdown_str = f"# {json_file_path.split('/')[-1].split('.')[0]}\n\n"

    # if 'classes' in module_dict:
    #     markdown_str += "## Classes\n\n"
    #     for class_dict in module_dict['classes']:
    #         markdown_str += f"### {class_dict['name']}\n\n"
    #         if class_dict['docstring']:
    #             markdown_str += f"{class_dict['docstring']}\n\n"
    #         markdown_str += "```python\n"
    #         markdown_str += f"class {class_dict['name']}:\n"
    #         for arg_dict in class_dict['args']:
    #             markdown_str += f"    {arg_dict['name']}: {arg_dict['type']}\n"
    #         for method_dict in class_dict['methods']:
    #             markdown_str += f"\n    def {method_dict['name']}("
    #             markdown_str += ', '.join([f"{arg['name']}: {arg['type']}" for arg in method_dict['args']])
    #             markdown_str += f") -> {method_dict['return_type']}:\n"
    #             if method_dict['docstring']:
    #                 markdown_str += f"        {method_dict['docstring']}\n"
    #         markdown_str += "```\n\n"

    # if 'functions' in module_dict:
    #     markdown_str += "## Functions\n\n"
    #     for function_dict in module_dict['functions']:
    #         markdown_str += f"### {function_dict['name']}()\n\n"
    #         if function_dict['docstring']:
    #             markdown_str += f"{function_dict['docstring']}\n\n"
    #         markdown_str += "```python\n"
    #         markdown_str += f"def {function_dict['name']}("
    #         markdown_str += ', '.join([f"{arg['name']}: {arg['type']}" for arg in function_dict['args']])
    #         markdown_str += f") -> {function_dict['return_type']}:\n"
    #         markdown_str += "```\n\n"

#     return markdown_str

# json_files
# json_file_path = 'docs/json/skyflow.vault._client.json'
# markdown_str = generate_markdown_from_json(json_file_path)
# print(markdown_str)


import os
import json

def generate_markdown_from_json(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            with open(file_path) as f:
                module_dict = json.load(f)

            path_arr = file_path.split('/')[-1].split('.')
            module_name = f"{path_arr[0]}"
            if path_arr[1] != "__init__":
                module_name += f".{path_arr[1]}"
            markdown_str = "{% env enable=\"pythonSdkRef\" %}\n\n"
            markdown_str += f"# {module_name}\n"

            if 'classes' in module_dict:
                # markdown_str += "## Classes\n\n"
                for class_dict in module_dict['classes']:
                    markdown_str += f"\n## Class: {class_dict['name']}\n\n"

                    if class_dict['docstring']:
                        markdown_str += f"{class_dict['docstring']}\n\n"
                    markdown_str += "```python\n"
                    markdown_str += f"class {class_dict['name']}:\n"
                    markdown_str += "```\n"

                    if class_dict['args']:
                        markdown_str += "\n#### Intializer Parameters\n"
                        markdown_str += "\n| Name | Type | Description |\n| --- | --- | --- |"
                        for arg_dict in class_dict['args']:
                            markdown_str += f"\n| {arg_dict['name']} | {arg_dict['type']}| {arg_dict['desc']} |"
                            # if(arg_dict['type'] != 'NoneType'):
                            #     markdown_str += f": {arg_dict['type']}\n"
                            # else:
                        markdown_str += "\n"
                    
                    if(class_dict['enum_values']):
                        values = class_dict['enum_values']
                        markdown_str += "\n#### Enumeration Members\n"
                        markdown_str += "\n| Name | Type |\n| --- | --- |"
                        markdown_str += ''.join([f"\n| {attr} | {value} |" for attr, value in values.items()])
                        markdown_str += "\n"

                    if class_dict['methods']:
                        markdown_str += f"\n\n## {class_dict['name']} Class Methods\n"
                        
                    for method_dict in class_dict['methods']:
                        markdown_str += f"\n### {method_dict['name']}\n"

                        if method_dict['docstring']:
                            markdown_str += f"\n{method_dict['docstring']}\n"

                        markdown_str += "\n```python\n"
                        markdown_str += f"def {method_dict['name']}("
    
                        if method_dict['args']:
                            for i, arg in enumerate(method_dict['args']):
                                markdown_str += f"{arg['name']}"
                                if arg['type']:
                                    markdown_str += f": {arg['type']}"
                                if i < len(method_dict['args']) - 1:
                                    markdown_str += ", "

                        markdown_str += ")"

                        if method_dict['return_type']:
                            markdown_str += f" -> {method_dict['return_type']}:\n"
                        else:
                            markdown_str += ":\n"
                        markdown_str += "```\n"

                        if method_dict['args']:
                            markdown_str += "\n#### Parameters\n"
                            markdown_str += "\n| Name | Type | Description |\n| --- | --- | --- |"
                            for i, arg in enumerate(method_dict['args']):
                                markdown_str += f"\n| {arg['name']} | {arg['type']}| {arg['desc']} |"
                            markdown_str += "\n"

                        markdown_str += "\n#### Returns\n"
                        if method_dict['return_type']:
                            markdown_str += f"{method_dict['return_type']}\n"
                        markdown_str += f"\n{method_dict['return_desc']}\n"

            if 'functions' in module_dict:
                markdown_str += "\n## Functions\n"
                for function_dict in module_dict['functions']:
                    markdown_str += f"\n### {function_dict['name']}\n\n"

                    if function_dict['docstring']:
                        markdown_str += f"{function_dict['docstring']}\n\n"
        
                    markdown_str += "```python\n"
                    markdown_str += f"def {function_dict['name']}("
                    # markdown_str += ', '.join([f"{arg['name']}: {arg['type']}" for arg in function_dict['args']])
                    if function_dict['args']:
                        for i, arg in enumerate(function_dict['args']):
                            markdown_str += f"{arg['name']}"
                            if arg['type']:
                                markdown_str += f": {arg['type']}"
                            if i < len(function_dict['args']) - 1:
                                markdown_str += ", "
                    markdown_str += ")"
                    if function_dict['return_type']:
                            markdown_str += f" -> {function_dict['return_type']}:\n"
                    else:
                        markdown_str += ":\n"
                    markdown_str += "```\n"

                    if function_dict['args']:
                        markdown_str += "\n#### Parameters\n"
                        markdown_str += "\n| Name | Type | Description |\n| --- | --- | --- |"
                        for i, arg in enumerate(function_dict['args']):
                            markdown_str += f"    \n| {arg['name']} | {arg['type']}| {arg['desc']} |"
                        markdown_str += "\n"

                    markdown_str += "\n#### Returns\n"
                    if function_dict['return_type']:
                        markdown_str += f"{function_dict['return_type']}\n"
                    markdown_str += f"\n{function_dict['return_desc']}\n"

            markdown_str += "\n{% /env %}"
            markdown_filename = module_name + ".md"
            markdown_file_path = os.path.join('docs/markdown', markdown_filename)
            with open(markdown_file_path, 'w') as f:
                f.write(markdown_str)
                print(f"Markdown file generated at {markdown_file_path}")

generate_markdown_from_json('docs/json')