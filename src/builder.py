import os
import shutil
import json
from time import sleep
from src.config import get_asset_auth_key, get_config_data
from src.util import group_directory, expand_into_directory, write_model_asset, AssetData, get_asset_url_from_id, get_file_hash, APPROVED_EXPORT_EXTENSIONS_REGISTRY, RemodelValue
from ropublisher import Publisher

def get_publisher() -> Publisher:
	config_data = get_config_data()
	return Publisher(
		asset_key=get_asset_auth_key(),
		group_id=config_data["build"]["publish"]["entity_id"],
		user_id=config_data["build"]["publish"]["entity_id"],
	)

def yield_for_asset_id(operation_id: str, is_verbose:bool) -> int | None:

	publisher = get_publisher()

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

def upload_image(asset_data: AssetData, is_verbose: bool) -> AssetData:
	config_data = get_config_data()
	source_path = asset_data["source"]
	if "operation_id" in asset_data and asset_data["operation_id"] != None and not asset_data["update_needed"]:
		return asset_data
	
	if not os.path.splitext(asset_data["source"])[1] in APPROVED_EXPORT_EXTENSIONS_REGISTRY["image"]:
	# if ext != ".png" and ext != ".jpeg" and ext != ".bmp" and ext != ".tga":
		return asset_data

	if is_verbose:
		print(f"uploading {source_path} to roblox")

	publisher = get_publisher()

	try:
		asset_data["operation_id"] = publisher.post_image(
			file_path=source_path, 
			name=os.path.splitext(os.path.relpath(source_path))[0], 
			publish_to_group=config_data["build"]["publish"]["publish_to_group"]
		)
	except:
		# might have had name filtered
		asset_data["operation_id"] = publisher.post_image(
			file_path=source_path, 
			name="api_uploaded_image", 
			publish_to_group=config_data["build"]["publish"]["publish_to_group"]
		)

	return asset_data

def upload_audio(asset_data: AssetData, is_verbose: bool) -> AssetData:
	config_data = get_config_data()
	source_path = asset_data["source"]
	# if ext != ".mp3" and ext != ".ogg":
	if not os.path.splitext(asset_data["source"])[1] in APPROVED_EXPORT_EXTENSIONS_REGISTRY["audio"]:
		return asset_data

	if "operation_id" in asset_data and asset_data["operation_id"] != None and not asset_data["update_needed"]:
		return asset_data
	
	if is_verbose:
		print(f"uploading {source_path} to roblox")

	publisher = get_publisher()

	try:
		asset_data["operation_id"] = publisher.post_image(
			file_path=source_path, 
			name=os.path.splitext(os.path.relpath(source_path))[0], 
			publish_to_group=config_data["build"]["publish"]["publish_to_group"]
		)
	except:
		# might have had name filtered
		asset_data["operation_id"] = publisher.post_image(
			file_path=source_path, 
			name="api_uploaded_image", 
			publish_to_group=config_data["build"]["publish"]["publish_to_group"]
		)

	return asset_data

def build_audio(asset_data: AssetData, build_path: str, is_verbose: bool, skip_upload: bool) -> AssetData:
	build_path = os.path.splitext(build_path)[0] + ".rbxm"

	if skip_upload:

		if not asset_data["update_needed"] and os.path.exists(build_path):
			# if is_verbose:
			# 	print(f"none needed {build_path}")
			return asset_data

	else:
		if "asset_id" in asset_data and asset_data["asset_id"] != None:
			if not asset_data["update_needed"] and os.path.exists(build_path):
				# if is_verbose:
				# 	print(f"none needed {build_path}")
				return asset_data	

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	sound_name = os.path.splitext(os.path.split(build_path)[1])[0]
	
	asset_id: None | int = None
	operation_id: None | str = None
	
	if "asset_id" in asset_data:
		asset_id = asset_data["asset_id"]

	if "operation_id" in asset_data:
		operation_id = asset_data["operation_id"]

	if (asset_id == None or asset_data["update_needed"]) and operation_id != None and not skip_upload:
		assert operation_id
		asset_id = yield_for_asset_id(operation_id, is_verbose)
		asset_data["asset_id"] = asset_id
	# else:
		# if is_verbose:
		# 	up_need = asset_data["update_needed"]
		# 	print(f"skipped yield {build_path} as asset_id == {asset_id} and update_needed == {up_need} and op_id == {operation_id}")

	if asset_id:
		asset_url = get_asset_url_from_id(asset_id)
		# if is_verbose:
			# print(f"got asset_url: {asset_url}")

		sound_params: dict[str, RemodelValue] = {
			"SoundId": {
				"type": "Content",
				"value": asset_url,
			},
			"Name": {
				"type": "String",
				"value": sound_name,
			}
		}
		
		if is_verbose:
			ext = os.path.splitext(build_path)[1][1:]
			print(f"writing sound {ext} file to: {build_path}")

		write_model_asset(build_path, "Sound", sound_params)	

		if not skip_upload:
			asset_data["update_needed"] = False	

	return asset_data		


def build_image(asset_data: AssetData, build_path: str, is_verbose: bool, skip_upload: bool) -> AssetData:
	if os.path.splitext(build_path)[1] == ".pdn":
		return asset_data

	build_path = os.path.splitext(build_path)[0] + ".txt"

	if skip_upload:

		if not asset_data["update_needed"] and os.path.exists(build_path):
			return asset_data

	else:
		if "asset_id" in asset_data and asset_data["asset_id"] != None:
			if not asset_data["update_needed"] and os.path.exists(build_path):
				return asset_data	


	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])


	asset_id: None | int = None
	operation_id: None | str = None
	if "asset_id" in asset_data:
		asset_id = asset_data["asset_id"]

	if "operation_id" in asset_data:
		operation_id = asset_data["operation_id"]

	if (asset_id == None or asset_data["update_needed"]) and operation_id != None and not skip_upload:
		assert operation_id
		asset_id = yield_for_asset_id(operation_id, is_verbose)
		asset_data["asset_id"] = asset_id

	if asset_id:

		if is_verbose:
			print(f"building {build_path}")
					
		if os.path.exists(build_path):
			os.remove(build_path)

		text = f"\"{get_asset_url_from_id(asset_id)}\""
		with open(build_path, "w") as file:
			file.write(text)

		if not skip_upload:
			asset_data["update_needed"] = False	

	return asset_data	

def build_animation(asset_data: AssetData, build_path: str, is_verbose: bool) -> AssetData:
	source_path = asset_data["source"]
	build_path = os.path.splitext(build_path)[0] + os.path.splitext(source_path)[1]

	if not asset_data["update_needed"] and os.path.exists(build_path):
		return asset_data

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.splitext(source_path)[1] == ".fbx":
		return asset_data
	else:

		if os.path.exists(build_path):
			os.remove(build_path)
			
		if is_verbose:
			print(f"building {build_path}")

		shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False	

	return asset_data	


def build_material(asset_data: AssetData, build_path: str, is_verbose: bool) -> AssetData:
	source_path = asset_data["source"]
	build_path = os.path.splitext(build_path)[0] + os.path.splitext(source_path)[1]
	
	if not asset_data["update_needed"] and os.path.exists(build_path):
		return asset_data
	
	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.exists(build_path):
		os.remove(build_path)
		
	if is_verbose:
		print(f"building {build_path}")

	shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False	

	return asset_data	

def build_mesh(asset_data: AssetData, build_path: str, is_verbose: bool) -> AssetData:
	source_path = asset_data["source"]
	build_path = os.path.splitext(build_path)[0] + ".rbxm"
	if not asset_data["update_needed"] and os.path.exists(build_path):
		return asset_data

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.splitext(source_path)[1] == ".fbx":
		return asset_data

	asset_data["update_needed"] = False	

	return asset_data	

def build_model(asset_data: AssetData, build_path: str, is_verbose: bool) -> AssetData:
	source_path = asset_data["source"]
	build_path = os.path.splitext(build_path)[0] + os.path.splitext(source_path)[1]
	if not asset_data["update_needed"] and os.path.exists(build_path):
		return asset_data

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.exists(build_path):
		os.remove(build_path)

	shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False

	return asset_data	

def build_particle(asset_data: AssetData, build_path: str, is_verbose: bool) -> AssetData:
	source_path = asset_data["source"]
	build_path = os.path.splitext(build_path)[0] + os.path.splitext(source_path)[1]
	if not asset_data["update_needed"] and os.path.exists(build_path):
		return asset_data

	if not os.path.exists(os.path.split(build_path)[0]):
		os.makedirs(os.path.split(build_path)[0])

	if os.path.exists(build_path):
		os.remove(build_path)

	shutil.copy(source_path, build_path)

	asset_data["update_needed"] = False	

	return asset_data	