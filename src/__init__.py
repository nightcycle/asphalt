import sys
import os
import multiprocessing
import json
import keyring
from src.audit import get_used_paths, update_lock_data
from src.config import init, LOCK_PATH, get_asset_auth_key, ROBLOX_ASSET_KEY_CREDENTIAL_NAME, ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME, get_lock_data
from src.util import expand_into_directory, group_directory, MODEL_EXTENSIONS, get_file_hash
from src.library import build_library_directory, build_library_module

def main():
	is_verbose = "-verbose" in sys.argv
	if sys.argv[1] == "init":
		init()
		
	elif sys.argv[1] == "update":

		is_efficient = "-efficient" in sys.argv	
		is_build = "-build" in sys.argv
		skip_upload = "-local" in sys.argv
		start_hash = get_file_hash(LOCK_PATH)
		if is_efficient:
			usage_registry = get_used_paths(is_verbose)
			update_lock_data(usage_registry=usage_registry, is_efficient=is_efficient, is_verbose=is_verbose, skip_upload=skip_upload)	
		else:
			update_lock_data(is_efficient=is_efficient, is_verbose=is_verbose, skip_upload=skip_upload)	
		finish_hash = get_file_hash(LOCK_PATH)
		if is_build:
			if start_hash != finish_hash:
				print("building module")
				build_library_directory(is_efficient, is_verbose, skip_upload)
				build_library_module(is_efficient, is_verbose)
			else:
				print("no changes detected, skipping module build")

	elif sys.argv[1] == "expand":

		model_path = sys.argv[2]
		folder_class = "Folder"
		if len(sys.argv) > 3:
			folder_class = sys.argv[3]

		expand_into_directory(model_path, folder_class)

	elif sys.argv[1] == "auth":
			keyring.set_password(ROBLOX_ASSET_KEY_CREDENTIAL_NAME, ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME, input("paste your open-cloud asset key: "))

	elif sys.argv[1] == "unpack":
		path = sys.argv[1]
		base, ext = os.path.splitext(path)
		if ext in MODEL_EXTENSIONS:
			if is_verbose:
				print(f"unpacking {path}")
			expand_into_directory(path)
		else:
			for sub_path, _sub_dir_names, file_names in os.walk(path):
				for file_name in file_names:
					file_path = os.path.join(sub_path, file_name).replace("\\", "/")
					if is_verbose:
						print(f"unpacking {file_path}")
					expand_into_directory(path)

# prevent from running twice
if __name__ == '__main__':
	multiprocessing.freeze_support()
	main()		
