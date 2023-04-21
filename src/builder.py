import os
import shutil
from time import sleep
from config import get_asset_auth_key, get_config_data
from util import group_directory, expand_into_directory, write_model_asset, AssetData, get_asset_url_from_id, get_file_hash
from ropublisher import Publisher

def yield_for_asset_id(publisher: Publisher, operation_id: int, is_verbose:bool) -> int | None:
	
	asset_id: None | int = None
	attempts = 0
	while asset_id == None and attempts < 10:
		sleep_duration = 0.5 + attempts*0.5
		sleep(sleep_duration)
		attempts += 1
		asset_id = publisher.get_asset_id_from_operations_id(operation_id)
		if is_verbose:
			print(f"attempted to get asset_id for {operation_id}, result = {asset_id}, delay = {sleep_duration}, attempt = {attempts}")

	return asset_id

def build_animation(asset_data: AssetData, build_path: str, is_verbose: bool):
	source_path = asset_data["source"]
	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.splitext(source_path)[1] == ".fbx":
		if is_verbose:
			print(f"can't auto import {source_path} yet")
	else:

		if os.path.exists(build_path):
			os.remove(build_path)
			
		if is_verbose:
			print(f"building {build_path}")

		shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False	

	return asset_data	


def build_audio(asset_data: AssetData, build_path: str, is_verbose: bool, skip_upload: bool):
	source_path = asset_data["source"]

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	build_path = os.path.splitext(build_path)[0] + ".rbxmx"

	sound_name = os.path.splitext(os.path.split(build_path)[1])[0]
	asset_id: None | int = None
	if not skip_upload:
		
		if is_verbose:
			print(f"uploading {build_path} to roblox")

		config_data = get_config_data()
		publisher = Publisher(
			asset_key=get_asset_auth_key(),
			group_id=config_data["build"]["publish"]["entity_id"],
			user_id=config_data["build"]["publish"]["entity_id"],
		)
		try:
			asset_data["operation_id"] = publisher.post_image(
				file_path=source_path, 
				name=os.path.splitext(os.path.relpath(source_path))[0], 
				publish_to_group=config_data["build"]["publish"]["publish_to_group"]
			)
		except:
			asset_data["operation_id"] = publisher.post_image(
				file_path=source_path, 
				name="name_was_moderated_so_we_named_it_this", 
				publish_to_group=config_data["build"]["publish"]["publish_to_group"]
			)
			
		asset_id: None | int = yield_for_asset_id(publisher, asset_data["operation_id"], is_verbose)
	else:
		asset_id = asset_data["asset_id"]

	if asset_id:
		asset_url = get_asset_url_from_id(asset_id)

		write_model_asset(build_path, "Sound", {
			"SoundId": {
				"type": "Content",
				"value": asset_url,
			},
			"Name": {
				"type": "String",
				"value": sound_name,
			}
		})	

		if not skip_upload:
			asset_data["update_needed"] = False	
	else:
		print(f"upload failed for {source_path}")

	return asset_data		

def build_image(asset_data: AssetData, build_path: str, is_verbose: bool, skip_upload: bool):
	source_path = asset_data["source"]

	if os.path.splitext(build_path)[1] == ".pdn":
		return 

	build_path = os.path.splitext(build_path)[0] + ".txt"


	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])
	asset_id: None | int = None
	if not skip_upload:
		config_data = get_config_data()
		if is_verbose:
			print(f"uploading {build_path} to roblox")

		publisher = Publisher(
			asset_key=get_asset_auth_key(),
			group_id=config_data["build"]["publish"]["entity_id"],
			user_id=config_data["build"]["publish"]["entity_id"],
		)
		try:
			asset_data["operation_id"] = publisher.post_image(
				file_path=source_path, 
				name=os.path.splitext(os.path.relpath(source_path))[0], 
				publish_to_group=config_data["build"]["publish"]["publish_to_group"]
			)
		except:
			asset_data["operation_id"] = publisher.post_image(
				file_path=source_path, 
				name="uploaded_instance", 
				publish_to_group=config_data["build"]["publish"]["publish_to_group"]
			)

		asset_id: None | int = yield_for_asset_id(publisher, asset_data["operation_id"], is_verbose)
	else:
		asset_id = asset_data["asset_id"]

	if os.path.exists(build_path):
		os.remove(build_path)

	if asset_id:

		if is_verbose:
			print(f"building {build_path}")

		text = f"\"{get_asset_url_from_id(asset_id)}\""
		with open(build_path, "w") as file:
			file.write(text)

		if not skip_upload:
			asset_data["update_needed"] = False	
	else:
		print(f"upload failed for {source_path}")

	return asset_data	

def build_material(asset_data: AssetData, build_path: str, is_verbose: bool):
	source_path = asset_data["source"]
	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.splitext(source_path)[1] == ".fbx":
		if is_verbose:
			print(f"can't auto import {source_path} yet")
	else:

		if os.path.exists(build_path):
			os.remove(build_path)
			
		if is_verbose:
			print(f"building {build_path}")

		shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False	

	return asset_data	

def build_mesh(asset_data: AssetData, build_path: str, is_verbose: bool):
	source_path = asset_data["source"]
	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.splitext(source_path)[1] == ".fbx":
		if is_verbose:
			print(f"can't auto import {source_path} yet")

	asset_data["update_needed"] = False	

	return asset_data	

def build_model(asset_data: AssetData, build_path: str, is_verbose: bool):
	source_path = asset_data["source"]

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.exists(build_path):
		os.remove(build_path)

	shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False

	return asset_data	

def build_particle(asset_data: AssetData, build_path: str, is_verbose: bool):
	source_path = asset_data["source"]

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.exists(build_path):
		os.remove(build_path)

	shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False	

	return asset_data	