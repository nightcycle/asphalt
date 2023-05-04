import os
import json
import hashlib
import base64
import shutil
import sys
from typing import TypedDict, Literal, Any

MODEL_EXTENSIONS = [".rbxm", ".rbxmx"]
APPROVED_EXPORT_EXTENSIONS_REGISTRY = {
	"audio": [".ogg", ".mp3"],
	"image": [".png",".jpeg", ".bmp", ".tga"],
	"material": MODEL_EXTENSIONS,
	"animation": MODEL_EXTENSIONS,
	"mesh": MODEL_EXTENSIONS,
	"model": MODEL_EXTENSIONS,
	"particle": MODEL_EXTENSIONS,
}

RemodelType = Literal[
	"String",
	"Content",
	"Bool",
	"Float64",
	"Float32",
	"Int64",
	"Int32",
	"CFrame",
	"Color3",
	"Vector3"
]

class AssetData(TypedDict):
	source: str
	hash: str
	asset_id: int | None
	operation_id: str | None
	update_needed: bool
	is_used: bool
	dependents: list[str] | None #used to determine if this is a source file, and which other files are built from it
	source_origin: str | None #used to determine if this was generated from another file, rather than the source

class RemodelValue(TypedDict):
	type: RemodelType
	value: Any

def get_data_file_path(file_name: str) -> str:
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base_path, f"data\\{file_name}").replace("\\", "/")

def run_exe_process(exe_name: str, args: list = [], silent=True):
	abs_path = get_data_file_path(exe_name)
	abs_dir = os.path.split(abs_path)[0]

	command = " ".join([abs_path] + args)

	if silent:
		command = command.replace("\"", "\\\"")
		bash_command = f"bash -c \"{command} > /dev/null 2>&1\""
		# print(f"bash_cmd: {bash_command}")
		os.system(bash_command)
	else:
		print("cmd: ",command)
		os.system(command)

def get_file_hash(path: str):
	with open(path, "rb") as file:
		return hashlib.sha256(file.read()).hexdigest()

def get_asset_url_from_id(asset_id: int):
	return f"rbxassetid://{asset_id}"

def convert_to_roblox_ext(file_path: str, goal_ext: str, is_model: bool) -> str:
	base, ext = os.path.splitext(file_path)
	if ext == goal_ext:
		return file_path
	else:
		out_path = base + goal_ext
		bool_str = str(is_model).lower()
		run_exe_process("remodel.exe", ["run", get_data_file_path("convert.remodel.lua"), file_path, out_path, bool_str])
		os.remove(file_path)
		return out_path

def convert_to_rbxl(file_path: str) -> str:
	return convert_to_roblox_ext(file_path, ".rbxl", False)

def convert_to_rbxlx(file_path: str) -> str:
	return convert_to_roblox_ext(file_path, ".rbxl", False)

def convert_to_rbxmx(file_path: str) -> str:
	return convert_to_roblox_ext(file_path, ".rbxl", True)

def convert_to_rbxm(file_path: str) -> str:
	return convert_to_roblox_ext(file_path, ".rbxm", True)

def group_directory(directory_path: str, folder_class_name="Folder", ext="rbxm", is_verbose=False):
	if ext[0] == ".":
		ext = ext[1:]
		
	file_path = directory_path + "." + ext
	if os.path.exists(file_path):
		os.remove(file_path)

	run_exe_process("remodel.exe", ["run", get_data_file_path("group_directory.remodel.lua"), directory_path, folder_class_name, ext], silent = not is_verbose)
	if folder_class_name=="SoundGroup":
		run_exe_process("rbxmk.exe", ["run", get_data_file_path("format_sound_tree.rbxmk.lua"), directory_path+"."+ext], silent = not is_verbose)
	shutil.rmtree(directory_path)

def expand_into_directory(model_file: str, folder_class_name="Folder", is_verbose=False):
	out_directory, ext_name = os.path.splitext(model_file)
	if not os.path.exists(out_directory):
		os.makedirs(out_directory)

	run_exe_process("remodel.exe", ["run", get_data_file_path("expand_instance.remodel.lua"), model_file, folder_class_name, out_directory, ext_name[1:]], silent = not is_verbose)

def write_model_asset(build_path: str, class_name: str, inst_config: dict[str, RemodelValue]):
	if "." in build_path:
		base, ext = os.path.splitext(build_path)
		build_path = base + ".rbxm"
	else:
		build_path = build_path + ".rbxm"


	if os.path.exists(build_path):
		os.remove(build_path)

	json_str = json.dumps(inst_config).replace("\n", "").replace(" ", "").replace("\"", "'")
	
	run_exe_process("remodel.exe", ["run", get_data_file_path("build_instance.remodel.lua"), build_path, class_name, f"\"{json_str}\""])

def decode_tags(bin_str: str) -> list[str]:
    def get_bytes_from_binary_str(bin_str: str) -> bytes:
        clean_data = bin_str.replace('![CDATA[', '').replace(']]', '').replace('\n', '').strip()
        return base64.b64decode(clean_data)

    def decode_binary_string(bin_str: str) -> list[int]:
        # Remove the CDATA tag and any newlines/whitespace
        output = []
        for b in get_bytes_from_binary_str(bin_str):
            output.append(int.from_bytes(bytes([b]), 'big'))
        return output

    def numbers_to_ascii_string(numbers_list: list[int]):
        # Convert the list of numbers to their corresponding ASCII characters
        ascii_string = ''.join(chr(num) for num in numbers_list)
        return ascii_string

    # Get the list of ASCII characters from the binary string
    ascii_tag_str = numbers_to_ascii_string(decode_binary_string(bin_str))

    # Split the ASCII string into a list of strings using the null character '\x00'
    return ascii_tag_str.split('\x00')

def encode_tags(tags: list[str]) -> str:
    def ascii_string_to_numbers(ascii_str: str) -> list[int]:
        # Convert each ASCII character to its corresponding integer value
        return [ord(char) for char in ascii_str]
    
    def numbers_to_binary_str(numbers_list: list[int]) -> bytes:
        # Convert each integer value to its corresponding byte
        return bytes(numbers_list)

    # Convert the list of ASCII strings into a single ASCII string separated by the null character '\x00'
    ascii_tag_str = '\x00'.join(tags)
    
    # Convert the ASCII string to its corresponding list of integer values
    numbers_list = ascii_string_to_numbers(ascii_tag_str)
    
    # Convert the list of integer values to its corresponding bytes
    byte_array = numbers_to_binary_str(numbers_list)
    
    # Encode the byte array into a base64 string
    base64_str = base64.b64encode(byte_array).decode('utf-8')
    
    return base64_str
