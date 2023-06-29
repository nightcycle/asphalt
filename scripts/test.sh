source .env/Scripts/Activate
sh scripts/to_exe.sh
# dist/asphalt.exe install
dist/asphalt.exe update -build -verbose -force -efficient
