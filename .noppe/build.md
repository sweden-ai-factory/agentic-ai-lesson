# Building the noppe image

noppe runs on x86 (`linux/amd64`) nodes, so the image is built for that
platform. The image is pushed to the Rahti project `agentic-ai-lesson-course`.
Run all commands from the repository root.

## 1. Log in to the Rahti registry

You need the OpenShift CLI `oc` for this (`brew install openshift-cli`, or
download it from the Rahti web console: **?** menu → **Command Line Tools**).
In the Rahti web console,
click your name in the top right, choose **Copy login command**, and run the
`oc login --token=... --server=...` command it shows. Then log Podman in to the
registry with your `oc` token:

```bash
podman login -u unused -p "$(oc whoami -t)" image-registry.apps.2.rahti.csc.fi
```

The token expires after about a day, so log in again before each build.

## 2. Build

Set the image name. Use the build date and time as the tag, so you can see which
image noppe runs and roll back if needed. Every build must get a new tag: if you
push again with a tag noppe already uses, noppe may keep running its cached copy
of the old image.

```bash
IMAGE=image-registry.apps.2.rahti.csc.fi/agentic-ai-lesson-course/agentic-ai-lesson:$(date +%Y-%m-%d-%H%M)
podman build --platform linux/amd64 -f .noppe/Dockerfile -t "$IMAGE" .
```

The build context is the repository root because the image copies
`pyproject.toml` files from it.

## 3. Verify

The architecture should be `amd64`, the hands-on packages should import, and the
Jupyter configuration should end with the settings for hidden files and the
start directory:

```bash
podman image inspect --format '{{.Architecture}}' "$IMAGE"
podman run --rm --platform linux/amd64 "$IMAGE" /opt/venv/bin/python -c 'import pydantic_ai; print(pydantic_ai.__version__)'
podman run --rm --platform linux/amd64 --entrypoint "" "$IMAGE" tail -n 2 /etc/jupyter/jupyter_server_config.py
```

Use the full path `/opt/venv/bin/python`. The image's start script activates
the Jupyter conda environment, so a plain `python` is conda's Python, which
does not have the hands-on packages. This is fine for the course, because
`uv run` uses `/opt/venv` (set by `UV_PROJECT_ENVIRONMENT`).

## 4. Push

```bash
podman push "$IMAGE"
oc get imagestreams -n agentic-ai-lesson-course
```

## 5. Use the image in noppe

Print the image name and enter it in the **Container image** field of the noppe
application (Manage workspaces → Applications → Edit application):

```bash
echo "$IMAGE"
```

Delete any running workspace and start a new one. It should open in
`agentic-ai-lesson/content/hands-on`, and the file browser should list
`.env.example`.

Images in a Rahti project are private by default. If noppe fails to pull the
image, allow anonymous pulls for the project (needed only once). This makes
**every** image in the project public, which is fine here because the image
contains no secrets (`.env` is not copied into it):

```bash
oc policy add-role-to-group system:image-puller system:unauthenticated -n agentic-ai-lesson-course
```
