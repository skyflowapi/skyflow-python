import inspect
import json
import importlib
import os
import re
from typing import get_origin, get_args, _GenericAlias
from typing import List, Tuple, Union
from enum import Enum
from docstring_parser import parse

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, _GenericAlias):
            return str(obj)
        elif isinstance(obj, type):
            return obj.__name__
        return json.JSONEncoder.default(self, obj)

# Generate JSON documentation for a Python SDK module.
def gen_json_for_module(modules, directory_path):
    for modulename in modules:
        module = importlib.import_module(modulename)

        module_dict = {}

        class_list = []
        function_list = []

        for name, member in inspect.getmembers(module):
            
            # Skip any members that are not functions or classes.
            if not inspect.isfunction(member) and not inspect.isclass(member):
                continue

            if 'skyflow' not in member.__module__ :
                continue

            if inspect.isclass(member):
                class_dict = {}
                class_dict['name'] = name
                class_dict['type'] = 'class'

                class_docstring = parse(inspect.getdoc(member))
                class_desc = get_desc(class_docstring)
                class_dict['docstring'] = class_desc

                
                enum_dict = None
                if(str(member.__class__) == "<class 'enum.EnumMeta'>"):
                    # enum_dict = {member:value for member, value in dict(member.__members__)}
                    enum_dict = {attr: get_param_type(value) for attr, value in dict(member.__members__).items()}

                class_dict['enum_values'] = enum_dict

                # Extracting class arguments 
                class_args = []
                for arg in inspect.getfullargspec(member.__init__).args[1:]:
                    arg_type = get_param_type(inspect.signature(member.__init__).parameters[arg].annotation)
                    arg_desc = get_param_desc(class_docstring, arg)
                    class_args.append({'name': arg, 'type': arg_type, 'desc': arg_desc})
                class_dict['args'] = class_args

                # Extracting class methods
                class_method_list = []
                for method_name, method_obj in inspect.getmembers(member, predicate=inspect.isfunction):
                    if method_name != '__init__' and 'skyflow' in method_obj.__module__ and not method_name.startswith('_'):
                        class_method_dict = {}
                        class_method_dict['name'] = method_name
                        class_method_dict['type'] = 'method'

                        method_docstring = parse(inspect.getdoc(method_obj))
                        method_desc = get_desc(method_docstring)
                        class_method_dict['docstring'] = method_desc
                        method_args = []


                        # Extracting method arguments
                        for arg in inspect.getfullargspec(method_obj).args[1:]:
                            arg_type = get_param_type(inspect.signature(method_obj).parameters[arg].annotation)
                            arg_desc = get_param_desc(method_docstring, arg)
                            method_args.append({'name': arg, 'type': arg_type, 'desc': arg_desc})
                        class_method_dict['args'] = method_args

                        # Extracting return type 
                        return_type = get_param_type(inspect.signature(method_obj).return_annotation)
                        if method_docstring.returns:
                            return_desc = method_docstring.returns.description
                        else:
                            return_desc = None

                        if return_type is not inspect._empty:
                            class_method_dict['return_type'] = return_type
                        class_method_dict['return_desc'] = return_desc

                        class_method_list.append(class_method_dict)

                class_dict['methods'] = class_method_list

                class_list.append(class_dict)
            # Generate JSON for the functions
            elif inspect.isfunction(member) and not name.startswith('_'):
                function_dict = {}
                function_dict['name'] = name
                function_dict['type'] = 'function'

                function_docstring = parse(inspect.getdoc(member))
                function_desc = get_desc(function_docstring)
                function_dict['docstring'] = function_desc
                function_args = []

                # Extracting function arguments
                for arg in inspect.getfullargspec(member).args:
                    arg_type = get_param_type(inspect.signature(member).parameters[arg].annotation)
                    arg_desc = get_param_desc(function_docstring, arg)
                    function_args.append({'name': arg, 'type': arg_type, 'desc': arg_desc})
                function_dict['args'] = function_args

                    # Extracting return type
                return_type = get_param_type(inspect.signature(member).return_annotation)

                if function_docstring.returns:
                    return_desc = function_docstring.returns.description
                else:
                    return_desc = None

                if return_type is not inspect._empty:
                    function_dict['return_type'] = return_type
                function_dict['return_desc'] = return_desc

                function_list.append(function_dict)

            if class_list:
                module_dict['classes'] = class_list

            if function_list:
                module_dict['functions'] = function_list

            # file_path = os.path.join(directory_path, f"{module.__name__}.json")
        
        file_path = os.path.join(directory_path, f"{module.__name__}.json")
        with open(f"{file_path}", 'w') as f:
            json.dump(module_dict, f, indent=2, cls=CustomJSONEncoder)

        print(f"JSON file generated at {file_path}")

def get_desc(parsed_docstring):
    if parsed_docstring.short_description and parsed_docstring.long_description:
        return parsed_docstring.short_description + "\n" + parsed_docstring.long_description
    elif parsed_docstring.short_description:
        return parsed_docstring.short_description
    else:
        return None

def get_param_desc(parsed_docstring, arg_name):
    for param in parsed_docstring.params:
        if param.arg_name == arg_name:
            return param.description
    return None

def get_param_type(param_type):
    if param_type == inspect._empty:
        param_type = None
    elif isinstance(param_type, type):
        param_type = param_type.__name__
    elif isinstance(param_type, tuple):
        param_type = tuple(get_type_name(t) for t in param_type)
    elif get_origin(param_type) == Union:
        param_type = " or ".join(get_type_name(t) for t in get_args(param_type))
    elif isinstance(param_type, List):
        param_type = List[get_type_name(get_args(param_type)[0])]
    elif isinstance(param_type, Enum):
        param_type = param_type.value
    
    return param_type

def get_type_name(param_type):
    if isinstance(param_type, type):
        return param_type.__name__
    elif isinstance(param_type, tuple):
        return tuple(get_type_name(t) for t in param_type)
    elif get_origin(param_type) == Union:
        return " or ".join(get_type_name(t) for t in get_args(param_type))
    elif isinstance(param_type, List):
        return List[get_type_name(get_args(param_type)[0])]
    elif hasattr(param_type, "__name__"):
        return param_type.__name__
    else:
        type_str = str(param_type)
        match = re.match(r"<class '(.+)'>", type_str)
        if match:
            return match.group(1)
        else:
            return type_str

modules = ['skyflow.vault.__init__', 'skyflow.service_account.__init__', 'skyflow.errors.__init__', 'skyflow.__init__']
# modules = ['skyflow.vault.__init__']
gen_json_for_module(modules, 'docs/json')



