import os
import subprocess
import requests

# Constants
DIST_FOLDER = './dist'
NEW_VERSIONS = os.environ["NEW_VERSIONS"]

if NEW_VERSIONS == "":
    print("no new versions available, NEW_VERSIONS env variable is empty")
    os.exit(1)

def get_existing_versions(files_dir):
    existing_versions = set()
    for file in os.listdir(files_dir):
        if file.endswith('.sh') and file.count('.') == 3:
            existing_versions.add('v' + file[:-3])
    return existing_versions

def generate_diffs(prev_version, current_version):
    print("executing add-new-version-script with PREVIOUS_ADD_DOCKER_VERSION: ",prev_version, 
    " ADD_DOCKER_VERSION",current_version)
    add_new_version_script_path = "./scripts/add-new-version"
    env_vars = {"PREVIOUS_ADD_DOCKER_VERSION": prev_version, "ADD_DOCKER_VERSION": current_version} 
    subprocess.run(["bash", add_new_version_script_path], check=True, env=env_vars)

# it will return a dictonary with key set to major.minor of a version and the
# value will be the greatest version for that major minor combination
def get_version_dict(versions):
    version_dict = {}

    for version in versions:
        if version.startswith('v'):
            version = version[1:]
        version_parts = version.split('.')
        major_minor = version_parts[0] + '.' + version_parts[1]
    
        if major_minor in version_dict:
            current_version = tuple(map(int, version_parts[2]))
            max_version = tuple(map(int, version_dict[major_minor].split('.')[2]))
            if current_version > max_version:
                version_dict[major_minor] = version
        else:
            version_dict[major_minor] = version

    return version_dict

def main():
    existing_versions = get_existing_versions(DIST_FOLDER)

    new_versions = NEW_VERSIONS.split(',')
    print("New Versions: ",new_versions)

    sorted_existing_versions = sorted(existing_versions)

    for version in new_versions:
        current_version = version[1:]
        prev_version = max(filter(lambda x: tuple(map(int, x[1:].split('.'))) < tuple(map(int, version[1:].split('.'))), sorted_existing_versions))
        prev_version = prev_version[1:]
        generate_diffs(prev_version, current_version)

    versions_string = ",".join(new_versions)
    print("running generate script")
    subprocess.run(["bash", "./scripts/generate"], check=True)

    version_dict = get_version_dict(new_versions)
    print("version dictionary for symlink: ",version_dict)

    for major_minor,version in version_dict.items():
        subprocess.call(['rm',f"{DIST_FOLDER}/{major_minor}.sh"])
        os.symlink(f"{version}.sh",f"{DIST_FOLDER}/{major_minor}.sh")

if __name__ == "__main__":
    main()