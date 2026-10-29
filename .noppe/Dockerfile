FROM image-registry.apps.2.rahti.csc.fi/noppe-public-images/jupyter-minimal:2025-09-16

# Install everything outside the home directory, which noppe may mount over.
ENV UV_INSTALL_DIR=/usr/local/bin \
    UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

USER root

# Install uv the same way as in content/setup.md
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the hands-on dependencies the same way as in content/setup.md (`uv sync`
# from the repository root). Only the project files are copied, so the workspace
# packages themselves are skipped; `uv run` installs them from the cloned repo.
WORKDIR /opt/agentic-ai-lesson
COPY pyproject.toml ./
COPY content/hands-on/pyproject.toml content/hands-on/.python-version content/hands-on/
RUN uv sync --no-install-workspace \
    && chown -R ${NB_UID}:${NB_GID} /opt/venv /opt/uv

# Show hidden files in the JupyterLab file browser, so students can edit .env
# (content/setup.md), and open JupyterLab in the hands-on directory of the
# repository that noppe clones into the home directory. Jupyter does not load
# server settings from jupyter_server_config.d, so they are added to
# jupyter_server_config.py. The start URL must be set on LabApp, because
# `jupyter lab` overrides ServerApp.default_url with LabApp.default_url. The
# base image has no overrides.json, so it is created here.
RUN printf '%s\n' '' \
        'c.ContentsManager.allow_hidden = True' \
        'c.LabApp.default_url = "/lab/tree/agentic-ai-lesson/content/hands-on"' \
        >> /etc/jupyter/jupyter_server_config.py \
    && mkdir -p ${CONDA_DIR}/share/jupyter/lab/settings \
    && echo '{"@jupyterlab/filebrowser-extension:browser": {"showHiddenFiles": true}}' \
        > ${CONDA_DIR}/share/jupyter/lab/settings/overrides.json

USER ${NB_UID}
WORKDIR /home/${NB_USER}
