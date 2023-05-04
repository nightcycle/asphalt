import os
import json
import re
from src.util import get_file_hash, APPROVED_EXPORT_EXTENSIONS_REGISTRY, AssetData
from luau.roblox.rojo import get_roblox_path_from_env_path
from src.config import get_config_data, MediaType, get_lock_data, set_lock_data, apply_import_data, LOCK_PATH
from typing import TypedDict, Any


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
	print(f"assembling asset indeces for efficient build")

	if is_verbose:
		print("scraping scripts for references to asphalt module and assets under it")

	config_data = get_config_data()
	build_roblox_path = get_roblox_path_from_env_path(config_data["build"]["module_path"])
	efficient_build_includes_all_local_files = config_data["build"]["efficient_build_includes_all_local_files"]
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
	if is_verbose:
		print("processing detected asphalt module references into formatted paths")

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
		print("asphalt asset references found")
		print(json.dumps(library_usages, indent=5))

	if efficient_build_includes_all_local_files:	
		if is_verbose:
			print("appending local files to usage list")

		local_path = os.path.abspath("")
		for media_type, possible_media_config in config_data["media"].items():
			untyped_media_source: Any = possible_media_config
			media_sources: list[str] = untyped_media_source["sources"]
			for media_source in media_sources:
				abs_media_source = os.path.abspath(media_source)
				if os.path.commonprefix([abs_media_source, local_path]) == local_path:
					for sub_path, sub_dir_names, file_names in os.walk(media_source):
						for file_name in file_names:
							file_path = os.path.join(sub_path, file_name).replace("\\", "/")
							if os.path.isfile(file_path):
								name, ext = os.path.split(file_name)
								dir_path = os.path.split(file_path)[0].replace(media_source.replace("\\", "/") + "/", "")
								final_path = dir_path
								
								if name != "":
									final_path +="/"+name

								final_path = media_type.title() + "/" + final_path
								usage_path_list.append(final_path)

	# if is_verbose:
		# print(f"\nusage_path_list: ")
		# print(json.dumps(usage_path_list, indent=5))

	if is_verbose:
		print("filtering usage paths to shortest common prefix")

	# deduplicate list
	usage_path_list = list(dict.fromkeys(usage_path_list).keys())
	if is_verbose:
		print("final usage paths:")
		print(json.dumps(usage_path_list, indent=5))

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

	if is_verbose:
		print("organizing file paths into media-type specific lists")

	media_usage_path_registry: dict = {}
	untyped_MediaType: Any = MediaType
	media_type_list: list = list(untyped_MediaType.__args__)
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

def update_lock_data(usage_registry: dict[MediaType, list[str]] = {}, is_verbose=False, is_efficient=False, skip_upload=False):
	reset_unused= not is_efficient
	config_data = get_config_data()
	lock_data = get_lock_data()
	print(f"updating {LOCK_PATH}")
	
	if is_verbose:
		print(f"importing specified lock files into {LOCK_PATH}")
	lock_data = apply_import_data(lock_data)

	if is_verbose:
		print("assembling map of files")

	# assemble a registry of all the hashes
	path_hash_registry: dict[MediaType, dict[str, CensusEntry]] = {}

	hash_lock_registry: dict[MediaType, dict[str, AssetData | None]] = {}
	for med_type, asset_reg in lock_data.items():
		untyped_med_type: Any = med_type
		if not untyped_med_type in hash_lock_registry:
			hash_lock_registry[untyped_med_type] = {}
		untyped_asset_reg: Any = asset_reg
		for path, asset_data in untyped_asset_reg.items():
			if not path in hash_lock_registry[untyped_med_type]:
				hash_lock_registry[untyped_med_type][path] = asset_data
			else:
				hash_lock_registry[untyped_med_type][path] = None

	for possible_media_type, possible_media_config in config_data["media"].items():
		untyped_media_type: Any = possible_media_type
		media_type: MediaType = untyped_media_type
		path_hash_registry[media_type] = {}
		untyped_media_source: Any = possible_media_config
		media_sources: list[str] = untyped_media_source["sources"]
		for dir_path in media_sources:

			for sub_path, _sub_dir_names, file_names in os.walk(dir_path):
				for file_name in file_names:
				
					file_path = os.path.join(sub_path, file_name).replace("\\", "/")
					short_path = file_path.replace(dir_path + "/", "")
				
					if short_path in path_hash_registry[media_type]:
						raise ValueError(f"duplicate path detected for {file_path}")
					hash_str = get_file_hash(file_path)
					path_hash_registry[media_type][short_path] = {
						"hash": hash_str,
						"dir_path": dir_path,
					}

	if is_verbose:
		print(f"comparing found file hashes and paths with {LOCK_PATH}")

	# update lock file with path-hash-registry
	for media_type, media_registry in path_hash_registry.items():
		approved_extension_list = APPROVED_EXPORT_EXTENSIONS_REGISTRY[media_type]
		if not media_type in lock_data:
			lock_data[media_type] = {}

		media_lock_tree = lock_data[media_type]
		med_hash_reg: dict[str, AssetData | None] = {}

		untyped_hash_reg: Any = hash_lock_registry
		if media_type in untyped_hash_reg:
			med_hash_reg = untyped_hash_reg[media_type]

		usage_paths = []
		if media_type in usage_registry:
			usage_paths = usage_registry[media_type]

		for media_path, entry in media_registry.items(): 
			key, ext = os.path.splitext(media_path)
			is_exportable = ext in approved_extension_list
			if not is_exportable:
				key = media_path #key + "_"+(ext[1:])
	
			if entry != None:
				if key in media_lock_tree and media_lock_tree[key] != None:
					# update previous entry
					lock_entry = media_lock_tree[key]
					old_hash = lock_entry["hash"]
					new_hash = entry["hash"]
					if old_hash != new_hash:
						if is_verbose:
							print(f"file changed: {media_path}")
							# print(f"key: {key}")
							# print(f"old_hash: {old_hash}")
							# print(f"new_hash: {new_hash}")

						lock_entry["hash"] = new_hash
						lock_entry["source"] = entry["dir_path"] + "/" + media_path
						lock_entry["update_needed"] = True
						if not skip_upload:
							lock_entry["asset_id"] = None
							lock_entry["operation_id"] = None
				elif not key in media_lock_tree:
					new_source = entry["dir_path"] + "/" + media_path
					asset_id: int | None = None
					dependents: None | list[str] = None
					if entry["hash"] in med_hash_reg and med_hash_reg[entry["hash"]] != None:
						lock_asset_data = med_hash_reg[entry["hash"]]
						assert lock_asset_data
						if not "source_origin" in lock_asset_data:
							# entry is renamed
							if is_verbose:
								old_source = lock_asset_data['source']
								print(f"file moved from {old_source} to {new_source}")

							if "asset_id" in lock_asset_data:
								asset_id = lock_asset_data["asset_id"]
							
							if "dependents" in lock_asset_data:
								dependents = lock_asset_data["dependents"]

					if asset_id == None and dependents == None:
						# add new entry
						if is_verbose:
							print(f"new file: {media_path}")

					media_lock_tree[key] = {
						"source": new_source,
						"hash": entry["hash"],
						"asset_id": asset_id,
						"operation_id": None,
						"update_needed": True,
						"is_used": True,
						"dependents": dependents,
						"source_origin": None
					}

			# reset if not used
			if not is_efficient:
				if media_lock_tree[key]["is_used"]:
					is_used = False
					for usage_path in usage_paths:
						if os.path.commonprefix([media_path, usage_path]) == usage_path:
							is_used = True

					if is_used == False and reset_unused:
						media_lock_tree[key]["is_used"] = False				


	# use the usage_paths to mass-update all used items
	if is_efficient:
		if is_verbose:
			print(f"setting usage state based on path prefixes gathered from scripts and configuration {LOCK_PATH}")
		for media_type, usage_paths in usage_registry.items():
			media_lock_tree = lock_data[media_type]
			for usage_path in usage_paths:
				for media_path in media_lock_tree:
					is_accessed_by_path = os.path.commonprefix([media_path, usage_path]) == usage_path
					if is_accessed_by_path:
						media_lock_tree[media_path]["is_used"] = True

	# update lock file
	set_lock_data(lock_data)	


