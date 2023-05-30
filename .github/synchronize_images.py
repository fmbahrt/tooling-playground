from subprocess import run


#run(["helm", "dep", "update", "cluster-addons/argocd/prod"], check=True)

results = run(["helm", "template", "cluster-addons/argocd/prod", "-f", "cluster-addons/argocd/prod/values.yaml"], capture_output=True, text=True).stdout

rendered_images = set([])

for line in iter(results.splitlines()):
    if "image:" in line:
        # Sanitize output
        image = line
        image = image.replace("image:", "")
        image = image.replace('''"''', "")
        image = image.strip()
        rendered_images.add(image)

docker_map = {
    'my.registry/argoproj/workflow-controller:v3.4.7': 'quay.io/argoproj/workflow-controller:v3.4.7',
    'my.registry/argoproj/argocd:v1.7.2': 'quay.io/argoproj/argocd:v1.7.2',
    'my.registry/argoproj/argocli:v3.4.7': 'quay.io/argoproj/argocli:v3.4.7',
    'my.registry/argoproj/argocd:v2.7.2': 'quay.io/argoproj/argocd:v2.7.2',
    'my.registry/redis:7.0.11-alpine': 'public.ecr.aws/docker/library/redis:7.0.11-alpine',
}

# Check if declared docker images covers the image rendered in Helm
declared_public_images = set(docker_map.keys())

image_diff = rendered_images - declared_public_images

# If this breaks - please revisit your Helm/Kustomize configurations and check if every possible image spec has been set.
# assert len(image_diff) == 0, f"Declared images does not cover the rendered images. Got diff {image_diff}."


# Pull, Retag and publish
for private, public in docker_map.items():
    # First we check if we try to sync an image that already exists in our target repository
    #run(["docker", "manifest", "inspect", private], check=True)
    print(f"docker manifest inspect {private}")
    run(["docker", "pull", public], check=True)
    run(["docker", "tag", public, private], check=True)
    #run(["docker", "push", private], check=True)
    print(f"docker push {private}")
