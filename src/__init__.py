import sys
import os
import keyring
from audit import get_used_paths, update_lock_data
from config import init, LOCK_PATH, get_asset_auth_key, ROBLOX_ASSET_KEY_CREDENTIAL_NAME, ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME
from util import expand_into_directory, group_directory
from library import build_library_directory, build_library_module

def main():
	if sys.argv[1] == "init":
		init()
		
	elif sys.argv[1] == "update":

		is_efficient = "-efficient" in sys.argv
		is_verbose = "-verbose" in sys.argv
		is_build = "-build" in sys.argv
		skip_upload = "-quick" in sys.argv
		print(f"updating {LOCK_PATH}")
		if is_efficient:
			update_lock_data(get_used_paths(is_verbose, is_efficient), is_efficient, is_verbose=is_verbose)	
		else:
			update_lock_data(is_efficient=is_efficient, is_verbose=is_verbose)	
		
		if is_build:
			build_library_directory(is_efficient, is_verbose, skip_upload)
			build_library_module(is_efficient, is_verbose)
	elif sys.argv[1] == "expand":

		model_path = sys.argv[2]
		folder_class = "Folder"
		if len(sys.argv) > 3:
			folder_class = sys.argv[3]

		expand_into_directory(model_path, folder_class)

	elif sys.argv[1] == "auth":
			keyring.set_password(ROBLOX_ASSET_KEY_CREDENTIAL_NAME, ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME, input("paste your open-cloud asset key: "))

	elif sys.argv[1] == "format":
		print("format")

main()