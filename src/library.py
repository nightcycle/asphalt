import shutil
import json
import os
import dpath
from luau.convert import mark_as_literal,from_any
from luau.roblox import write_script
from luau.path import remove_all_path_variants
from luau.roblox.util import get_module_require, get_instance_from_path
from luau.roblox.rojo import get_roblox_path_from_env_path, build_sourcemap, get_rojo_project_path
from src.util import AssetData
from src.config import get_lock_data, get_config_data, set_lock_data, MediaType
from src.builder import build_animation, build_audio, build_image, build_material, build_mesh, build_model, build_particle, upload_audio, upload_image
from typing import Any

def get_dir_paths_by_media_type() -> dict[MediaType, str]:
	config_data = get_config_data()
	build_path = config_data['build']['dir_path']
	path_dir: dict[Any, str] = {}
	for media_type, media_data in config_data["media"].items():
		untyped_med_data: Any = media_data
		if "dir_path" in untyped_med_data:
			path_dir[media_type] = untyped_med_data["dir_path"]
		else:
			path_dir[media_type] = config_data["build"]["dir_path"]+"/"+media_type.title()

	return path_dir	

def build_library_directory(is_efficient: bool, is_verbose: bool, skip_upload: bool, force_upload: bool):

	config_data = get_config_data()
	lock_data = get_lock_data()
	dir_path_registry = get_dir_paths_by_media_type()
	print("editing directory")
	
	if is_efficient:
		for media_type, dir_path in dir_path_registry.items():
			if os.path.exists(dir_path):
				if is_verbose:
					print(f"erasing previous {dir_path}")
				shutil.rmtree(dir_path)
				os.makedirs(dir_path)

	if not skip_upload or force_upload:	
		if is_verbose:
			print("uploading audio assets")
		for path, entry in lock_data['audio'].items():
			if not 'asset_id' in entry or entry['asset_id'] == None:
				# if is_verbose:
				# 	print(f"\nuploading {path} with {skip_upload} and {is_efficient}")
				# 	print(json.dumps(entry))
				try:
					lock_data['audio'][path] = upload_audio(entry, is_verbose)
				except:
					print(f"audio upload failed: {path}")

		if is_verbose:
			print("uploading image assets")

		for path, entry in lock_data['image'].items():
			if not 'asset_id' in entry or entry['asset_id'] == None:
				try:
					lock_data['image'][path] = upload_image(entry, is_verbose)
				except:
					print(f"image upload failed: {path}")

	if is_verbose:
		print("building animation dir")

	for path, entry in lock_data['animation'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['animation'][path] = build_animation(entry, dir_path_registry["animation"] + "/" + path, is_verbose)

	if is_verbose:
		print("building audio dir")


	for path, entry in lock_data['audio'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['audio'][path] = build_audio(entry, dir_path_registry["audio"] + "/" + path, is_verbose, skip_upload)

	if is_verbose:
		print("building image dir")

	for path, entry in lock_data['image'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['image'][path] = build_image(entry, dir_path_registry["image"] + "/" + path, is_verbose, skip_upload)


	if is_verbose:
		print("building material dir")

	for path, entry in lock_data['material'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['material'][path] = build_material(entry, dir_path_registry["material"] + "/" + path, is_verbose)

	if is_verbose:
		print("building mesh dir")

	for path, entry in lock_data['mesh'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['mesh'][path] = build_mesh(entry, dir_path_registry["mesh"] + "/" + path, is_verbose)

	if is_verbose:
		print("building model dir")

	for path, entry in lock_data['model'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['model'][path] = build_model(entry, dir_path_registry["model"] + "/" + path, is_verbose)

	if is_verbose:
		print("building particle dir")

	for path, entry in lock_data['particle'].items():
		if not is_efficient or entry['is_used']:	
			lock_data['particle'][path] = build_particle(entry, dir_path_registry["particle"] + "/" + path, is_verbose)

	if is_verbose:
		print("setting lock data")

	set_lock_data(lock_data)

def build_library_module(is_efficient: bool, is_verbose: bool):
	config_data = get_config_data()
	lock_data = get_lock_data()
	build_path = config_data['build']['module_path']
	dir_path_registry = get_dir_paths_by_media_type()
	module_name = os.path.splitext(os.path.split(build_path)[1])[0]
	# path_registry = {}
	module_registry: dict = {}
	tree_registry: dict = {}
	if is_verbose:
		print("converting paths to roblox instance indeces")

	# adding asset including modules
	for media_type, dir_path in dir_path_registry.items():
		base_path = ""
		try:
			base_path = get_roblox_path_from_env_path(dir_path)
		except:
			base_path = get_roblox_path_from_env_path(dir_path+".rbxm")
		
		for sub_path, _sub_dir_names, file_names in os.walk(dir_path):
			for file_name in file_names:
				file_path = os.path.join(sub_path, file_name).replace("\\", "/")
				base, ext = os.path.splitext(file_path)
				name = os.path.splitext(file_name)[0]
				roblox_path = base_path + "/" + os.path.splitext(file_path.replace(dir_path+"/", ""))[0]
				key_path = module_name + "/" + str(media_type).title() + "/" + roblox_path.replace(base_path+"/", "")
				par_dir_path = os.path.split(key_path)[0]
				is_safe_to_add = True
				
				if is_efficient:
					post_media_path = os.path.splitext("/".join(key_path.split("/")[1:]))[0]
					if media_type in lock_data:
						untyped_lock_data: Any = lock_data
						lock_registry = untyped_lock_data[media_type]
						if post_media_path in lock_registry:
							asset_data: AssetData = lock_registry[post_media_path]
							if not asset_data["is_used"]:
								is_safe_to_add = False

				if is_safe_to_add:
					if not par_dir_path in module_registry:
						module_registry[par_dir_path] = {}

					out_type: str | None = None
					if media_type == "model":
						out_type = "Instance"
					elif media_type == "animation":
						out_type = "Animation"
					elif media_type == "audio":
						out_type = "Sound"
					# elif start_media_type == "Image":
					elif media_type == "material":
						out_type = "MaterialVariant"	
					elif media_type == "particle":	
						out_type = "ParticleEmitter"	

					type_suffix = ""
					if out_type != None:
						type_suffix = f" :: {out_type}"

					# print(start_media_type, out_type, type_suffix)

					# print(par_dir_path)
					if ext == ".txt":
						with open(file_path, "r") as file:
							module_registry[par_dir_path][name] = mark_as_literal(file.read() + type_suffix)
							dpath.new(tree_registry, par_dir_path, {})

					elif ext == ".rbxmx" or ext == ".rbxm":
						module_registry[par_dir_path][name] = mark_as_literal(get_instance_from_path(roblox_path) + type_suffix)
						dpath.new(tree_registry, par_dir_path, {})

	# registering middle-modules
	if is_verbose:
		print("registering middle modules")
	
	for path, value in dpath.search(tree_registry, '**', yielded=True):
		if not path in module_registry:
			module_registry[path] = {}

	# adding requires to modules
	if is_verbose:
		print("connecting middle modules")

	for path, registry in module_registry.items():
		for sub_path in module_registry:
			dir_path, name = os.path.split(sub_path)
			if dir_path == path:
				if not name in registry:
					registry[name] = mark_as_literal(f"require(script:WaitForChild(\"{name}\"))")

	# building modules
	if is_verbose:
		print("building module scripts")

	build_base, build_ext = os.path.splitext(build_path)
	remove_all_path_variants(build_path)

	build_order: list[str] = list(module_registry.keys())
	build_order.sort()

	for path in build_order:

		registry = module_registry[path]

		tree_content = "return " + from_any(registry, skip_initial_indent=True)
		get_rep_str = "game:GetService(\"ReplicatedStorage\")"
		rep_var_name = "ReplicatedStorage"
		tree_content = tree_content.replace(get_rep_str, rep_var_name)
		content = [
			"--!strict",
			"-- Do not edit - this script was generated by @nightcycle/asphalt"
		]
		if rep_var_name in tree_content:
			content.append(f"local {rep_var_name} = {get_rep_str}")
		content.append(tree_content)
		module_build_path = os.path.split(build_base)[0] + "/" + path + build_ext
		if is_verbose:
			print(f"building {module_build_path}")
		write_script(module_build_path, "\n".join(content), write_as_directory=True, skip_source_map=True)
		# if is_verbose:
		# 	print(f"building {module_build_path}")

	# with open("module_registry.json", "w") as mod_file:
	# 	mod_file.write(json.dumps(module_registry, indent=5))

	# with open("tree_registry.json", "w") as tree_file:
	# 	tree_file.write(json.dumps(tree_registry, indent=5))

	build_sourcemap(get_rojo_project_path())
