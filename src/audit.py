import os
import json
import re
from util import get_file_hash
from luau.roblox.rojo import get_roblox_path_from_env_path
from config import get_config_data, MediaType, get_lock_data, set_lock_data
from typing import TypedDict

class CensusEntry(TypedDict):
	hash: str
	dir_path: str

def get_require_path(pattern: str):
	if "=" in pattern:
		pattern = pattern.split("=")[1]

	pattern = pattern.replace("require", "").replace("WaitForChild", "").replace("FindFirstChild", "")
	pattern = pattern.replace("GetService", "").replace("FindService", "")
	keywords = re.findall(r'"([^"]+)"|(\.?\w+)', pattern)
	# Flatten the list of tuples and filter out None values
	keywords = [keyword for group in keywords for keyword in group if keyword]
	# Remove leading dot (if any)
	keywords = [keyword.lstrip('.') for keyword in keywords]

	ro_path = "/".join(keywords)

	# print(pattern, " => ", ro_path)


	return ro_path

def extract_library_statements(input_string: str, library_var_name: str):
	# Split the input string into lines
	lines = input_string.split('\n')
	
	# Define a regular expression pattern to match the statements starting with "Library"
	#     pattern = re.compile(rf'\b{library_var_name}\.[\w.]+\b')
	pattern = re.compile(rf'\b{library_var_name}(\.\w+|\["[\w\s]+"\])+')

	# Initialize a list to store the extracted statements
	extracted_statements = []
	
	# Iterate over each line to find the matches
	for line in lines:
		match = pattern.search(line)
		if match:
			extracted_statements.append(match.group())

	return extracted_statements

def get_used_paths(is_verbose=False) -> dict[MediaType, list[str]]:
	config_data = get_config_data()
	build_roblox_path = get_roblox_path_from_env_path(config_data["build"]["module_path"])
	
	script_paths = []

	# get the scripts that seem to require the built module
	for script_dir in config_data["build"]["asset_usage_audit_script_directories"]:
		for sub_path, sub_dir_names, file_names in os.walk(script_dir):
			for file_name in file_names:
				file_path = os.path.join(sub_path, file_name).replace("\\", "/")
				base, ext = os.path.splitext(file_path)
				if ext == ".luau" or ext == ".lua":
					if file_path != config_data["build"]["module_path"]:
						script_paths.append(file_path)

	# get the paths used in those scripts
	library_usages = {}
	usage_path_list = []
	for script_path in script_paths:
		with open(script_path, "r") as script_file:
			content_str = script_file.read()
			content = content_str.split("\n")

			# get if built module is required
			for line in content:
				if "require" in line and "=" in line:
					require_path = get_require_path(line)
					if require_path == build_roblox_path:

						# get variable the built module was assigned to
						variable_name = (line.split("=")[0]).replace("local", "").replace(" ", "").replace("\t", "")
						
						# extract the references that variable and the follow paths provided
						extractions = extract_library_statements(content_str, variable_name)
						
						# filter and format the extractions to be path format
						filtered_extractions = []
						for extraction in extractions:
							filtered_extraction = extraction.replace(variable_name, "")
							if filtered_extraction[0] == ".":
								filtered_extraction = filtered_extraction[1:]

							filtered_extraction = filtered_extraction.replace(".", "/")
							filtered_extractions.append(filtered_extraction)

						# assign those extractions to the registry for later processing 
						if is_verbose:
							library_usages[script_path] = filtered_extractions

						usage_path_list += filtered_extractions

	if is_verbose:
		print("module references found")
		print(json.dumps(library_usages, indent=5))
	
	# deduplicate list
	usage_path_list = list(dict.fromkeys(usage_path_list).keys())

	efficient_path_list = []
	for usage_path in usage_path_list:
		is_best_path = True
		for sub_path in usage_path_list:
			if sub_path != usage_path:
				uses_sub_path = os.path.commonprefix([usage_path, sub_path]) == sub_path
				if uses_sub_path:
					is_best_path = False
		if is_best_path:
			efficient_path_list.append(usage_path)
				
	# if is_verbose:
	# 	print("usage path list")
	# 	print(json.dumps(efficient_path_list, indent=5))

	media_usage_path_registry = {}
	media_type_list = list(MediaType.__args__)
	for usage_path in efficient_path_list:
		keys = usage_path.split("/")
		media_type = keys[0].lower()
		if media_type in media_type_list:
			formatted_path = "/".join(keys[1:])
			if not media_type in media_usage_path_registry:
				media_usage_path_registry[media_type] = []
			media_usage_path_registry[media_type].append(formatted_path)
	
	if is_verbose:
		print("media sorted path list")
		print(json.dumps(media_usage_path_registry, indent=5))
		
	return media_usage_path_registry

def update_lock_data(usage_registry: dict[MediaType, list[str]] = {}, reset_unused=False) -> dict[str, str]:
	config_data = get_config_data()
	lock_data = get_lock_data()
	
	# assemble a registry of all the hashes
	path_hash_registry: dict[MediaType, dict[str, CensusEntry]] = {}
	for media_type, path_list in config_data["media"].items():
		path_hash_registry[media_type] = {}
		for dir_path in path_list:
			for sub_path, _sub_dir_names, file_names in os.walk(dir_path):
				for file_name in file_names:
					file_path = os.path.join(sub_path, file_name).replace("\\", "/")
					short_path = file_path.replace(dir_path + "/", "")
					
					if short_path in path_hash_registry[media_type]:
						raise ValueError(f"duplicate path detected for {file_path}")
					
					path_hash_registry[media_type][short_path] = {
						"hash": get_file_hash(file_path),
						"dir_path": dir_path,
					}

	# update lock file with path-hash-registry
	for media_type, media_registry in path_hash_registry.items():
		media_lock_tree = lock_data[media_type]
		
		usage_paths = []
		if media_type in usage_registry:
			usage_paths = usage_registry[media_type]

		for media_path, entry in media_registry.items(): 
			if media_path in media_lock_tree:
				# update previous entry
				lock_entry = media_lock_tree[media_path]
				if lock_entry["hash"] != entry["hash"]:
					lock_entry["hash"] = entry["hash"]
					lock_entry["path"] = entry["dir_path"] + "/" + media_path
					lock_entry["update_needed"] = True
			else:
				# add new entry
				media_lock_tree[media_path] = {
					"source": entry["dir_path"] + "/" + media_path,
					"hash": entry["hash"],
					"asset_id": None,
					"operation_id": None,
					"update_needed": True,
					"is_used": False,
				}

			# reset if not used
			if media_lock_tree[media_path]["is_used"]:
				is_used = False
				for usage_path in usage_paths:
					if os.path.commonprefix([media_path, usage_path]) == usage_path:
						is_used = True

				if is_used == False and reset_unused:
					media_lock_tree[media_path]["is_used"] = False				

	# use the usage_paths to mass-update all used items
	for media_type, usage_paths in usage_registry.items():
		media_lock_tree = lock_data[media_type]
		for usage_path in usage_paths:
			for media_path in media_lock_tree:
				is_accessed_by_path = os.path.commonprefix([media_path, usage_path]) == usage_path
				if is_accessed_by_path:
					media_lock_tree[media_path]["is_used"] = True

	# update lock file
	set_lock_data(lock_data)	