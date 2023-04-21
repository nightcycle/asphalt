import shutil
import json
import os
from luau.convert import mark_as_literal,from_any
from luau.roblox.util import get_module_require, get_instance_from_path
from luau.roblox.rojo import get_roblox_path_from_env_path
from config import get_lock_data, get_config_data, set_lock_data

# from audit import get_file_hash
from builder import build_animation, build_audio, build_image, build_material, build_mesh, build_model, build_particle

def build_library_directory(is_efficient: bool, is_verbose: bool, skip_upload: bool):

	config_data = get_config_data()
	lock_data = get_lock_data()
	build_path = config_data['build']['dir_path']
	
	print(f"editing {build_path} directory")
	
	for path, entry in lock_data['animation'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['animation'][path] = build_animation(entry, build_path + "/Animation/" + path, is_verbose)

	for path, entry in lock_data['audio'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['audio'][path] = build_audio(entry, build_path + "/Audio/" + path, is_verbose, skip_upload)
			set_lock_data(lock_data)

	for path, entry in lock_data['image'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['image'][path] = build_image(entry, build_path + "/Image/" + path, is_verbose, skip_upload)
			set_lock_data(lock_data)

	for path, entry in lock_data['material'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['material'][path] = build_material(entry, build_path + "/Material/" + path, is_verbose)

	for path, entry in lock_data['mesh'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['mesh'][path] = build_mesh(entry, build_path + "/Mesh/" + path, is_verbose)

	for path, entry in lock_data['model'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['model'][path] = build_model(entry, build_path + "/Model/" + path, is_verbose)

	for path, entry in lock_data['particle'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['particle'][path] = build_particle(entry, build_path + "/Particle/" + path, is_verbose)

	set_lock_data(lock_data)

def build_library_module(is_efficient: bool, is_verbose: bool):
	config_data = get_config_data()
	build_path = config_data['build']['module_path']
	dir_path = config_data['build']['dir_path']

	base_path = get_roblox_path_from_env_path(dir_path)

	# path_registry = {}
	module_registry = {}

	for sub_path, _sub_dir_names, file_names in os.walk(dir_path):
		for file_name in file_names:
			file_path = os.path.join(sub_path, file_name).replace("\\", "/")
			base, ext = os.path.splitext(file_path)
			name = os.path.splitext(os.path.split(file_path)[1])[0]
			roblox_path = get_roblox_path_from_env_path(base)

			key_path = roblox_path.replace(base_path+"/", "")
			par_dir_path = "/".join(key_path.split("/")[0:(len(key_path.split("/"))-1)])
			if not par_dir_path in module_registry:
				module_registry[par_dir_path] = {}

			if ext == ".txt":
				with open(file_path, "r") as file:
					module_registry[par_dir_path][name] = mark_as_literal(file.read())
			elif ext == ".rbxmx" or ext == ".rbxm":
				module_registry[par_dir_path][name] = mark_as_literal(get_instance_from_path(roblox_path))

	if is_verbose:
		print(from_any(module_registry, skip_initial_indent=False))
		# print(json.dumps(path_registry, indent=5))