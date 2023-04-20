import shutil
import os
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
			lock_data['animation'][path] = build_animation(entry, build_path + "/animation/" + path, is_verbose, skip_upload)

	for path, entry in lock_data['audio'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['audio'][path] = build_audio(entry, build_path + "/audio/" + path, is_verbose, skip_upload)

	for path, entry in lock_data['image'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['image'][path] = build_image(entry, build_path + "/image/" + path, is_verbose, skip_upload)

	for path, entry in lock_data['material'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['material'][path] = build_material(entry, build_path + "/material/" + path, is_verbose, skip_upload)

	for path, entry in lock_data['mesh'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['mesh'][path] = build_mesh(entry, build_path + "/mesh/" + path, is_verbose, skip_upload)

	for path, entry in lock_data['model'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['model'][path] = build_model(entry, build_path + "/model/" + path, is_verbose)

	for path, entry in lock_data['particle'].items():
		if entry['update_needed'] and (not is_efficient or entry['is_used']):	
			lock_data['particle'][path] = build_particle(entry, build_path + "/particle/" + path, is_verbose, skip_upload)

	set_lock_data(lock_data)