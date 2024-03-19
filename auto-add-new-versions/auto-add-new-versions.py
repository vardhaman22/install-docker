import os
import subprocess
import requests

# Constants
DIST_FOLDER = './dist'
EXCLUDED_VERSIONS = 'v20.10.25,v20.10.26,v20.10.27,v23.0.7,v23.0.8,v23.0.9'

def get_existing_versions(files_dir):
    existing_versions = set()
    for file in os.listdir(files_dir):
        if file.endswith('.sh') and file.count('.') == 3:
            existing_versions.add('v' + file[:-3])
    return existing_versions

def get_latest_major_minor_versions(existing_versions):
    major_minor_versions = set()
    for version in existing_versions:
        major_minor_versions.add(version[1:-4])
    return major_minor_versions

def fetch_ten_latest_github_releases(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        releases = [release for release in response.json() if not release.get('prerelease')]
        return sorted(releases, key=lambda x: x['created_at'], reverse=True)[:10]
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch releases: {e}")
        return None

def generate_diffs(prev_version, current_version):
    add_new_version_script_path = "./scripts/add-new-version"
    env_vars = {"PREVIOUS_ADD_DOCKER_VERSION": prev_version, "ADD_DOCKER_VERSION": current_version} 
    subprocess.run(["bash", add_new_version_script_path], check=True, env=env_vars)

def main():
    existing_versions = get_existing_versions(DIST_FOLDER)
    major_minor_versions = get_latest_major_minor_versions(existing_versions)
    owner = "moby"
    repo = "moby"
    ten_latest_releases = fetch_ten_latest_github_releases(owner, repo)
    ten_latest_versions = [release['tag_name'] for release in ten_latest_releases]
    excluded_versions = set(EXCLUDED_VERSIONS.split(","))
    print(excluded_versions)
    new_versions = set(ten_latest_versions) - existing_versions - excluded_versions
    print(new_versions)

    sorted_existing_versions = sorted(existing_versions)
    for version in new_versions:
        current_version = version[1:]
        prev_version = max(filter(lambda x: tuple(map(int, x[1:].split('.'))) < tuple(map(int, version[1:].split('.'))), sorted_existing_versions))
        prev_version = prev_version[1:]
        generate_diffs(prev_version, current_version)

    versions_string = ",".join(new_versions)
    PR_TITLE = "Add docker " + versions_string
    # subprocess.run(["bash", "./scripts/generate"], check=True)
    os.environ["PR_TITLE"] = "1"


if __name__ == "__main__":
    main()