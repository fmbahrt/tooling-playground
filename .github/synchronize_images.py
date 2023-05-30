import argparse
import json

from pathlib import Path
from subprocess import run


def initialize_helm(root):
    values_file = root / "values.yaml"
    assert values_file.is_file(), f"{values_file} is not a file."
    # Start by updating dependencies - we need that for rendering
    run(["helm", "dep", "update", root], check=True)
    

def initialize_engine(engine, root):
    if engine == "helm":
        initialize_helm(root)
    else:
        raise NotImplementedError("Engine not implemented")


def fetch_images_helm(root):
    results = run(["helm", "template", root, "-f", root / "values.yaml"], capture_output=True, text=True).stdout
    
    rendered_images = set([])
    
    for line in iter(results.splitlines()):
        if "image:" in line:
            # Sanitize output
            image = line
            image = image.replace("image:", "")
            image = image.replace('''"''', "")
            image = image.strip()
            rendered_images.add(image)

    return rendered_images


def fetch_images(engine, root):
    if engine == "helm":
        return fetch_images_helm(root)
    else:
        raise NotImplementedError("Engine not implemented")


def synchronize_images(image_mappings):
    for private, public in image_mappings.items():
        # First we check if we try to sync an image that already exists in our target repository
        #run(["docker", "manifest", "inspect", private], check=True)
        print(f"docker manifest inspect {private}")
        run(["docker", "pull", public], check=True)
        run(["docker", "tag", public, private], check=True)
        #run(["docker", "push", private], check=True)
        print(f"docker push {private}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Synchronize Docker images between registries.",
        epilog="Maintained by devops@supwiz.com",
    )

    parser.add_argument( # Project root dir
        "root",
        type=str,
        help="Root dir of the deployment",
        nargs=1,
    )
    parser.add_argument(
        "--engine",
        default="helm",
        choices=["helm"],
        help="Which rendering engine to use.",
    )
    parser.add_argument(
        "--check-declared-images",
        action="store_true",
        help="check if the declared images covers the rendered images",
    )
    parser.add_argument(
        "--synchronize",
        action="store_true",
        help="Synchronize images between registries",
    )

    args = parser.parse_args()

    root_path = Path(args.root[0])
    assert root_path.is_dir()

    image_mappings_path = root_path/ "workflow_docker_mappings.yaml"
    with open(image_mappings_path) as json_file:
        declared_public_images = json.load(json_file)

    # Assert missing images in mappings
    if args.check_declared_images:

        # Start by initializing the engine
        initialize_engine(args.engine, root_path)

        # Fetch all rendered images
        rendered_images = fetch_images(args.engine, root_path) 

        image_diff = rendered_images - declared_public_images 
        assert len(image_diff) == 0, f"Declared images does not cover the rendered images. Got diff {image_diff}."

    # Synchronize images
    if args.synchronize:
        synchronize_images(image_mappings)
