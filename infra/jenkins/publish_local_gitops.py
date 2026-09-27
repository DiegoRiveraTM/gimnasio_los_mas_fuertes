"""Publish tested manifests to deploy/local; never apply Kubernetes resources."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml


REPOSITORY = "https://github.com/DiegoRiveraTM/gimnasio_los_mas_fuertes.git"
BRANCH = "deploy/local"
SERVICES = ("auth-service", "membership-service", "access-qr-service")
PATHS = ("infra/kubernetes/base", "infra/kubernetes/overlays/local")


def run(*args, cwd=None, env=None, capture=False):
    return subprocess.run(
        args, cwd=cwd, env=env, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    )


def update_images(config, tag):
    if not tag.isdigit() or int(tag) < 1:
        raise ValueError("Expected a positive Jenkins build number")
    images = config.get("images", [])
    for service in SERVICES:
        matches = [item for item in images if item.get("newName") == f"gym-lmf/{service}"]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one image mapping for {service}")
        if "digest" in matches[0]:
            raise ValueError("Digest-based images need a different publication strategy")
    for item in images:
        if item.get("newName") in {f"gym-lmf/{s}" for s in SERVICES}:
            item["newTag"] = tag
    return config


def main():
    tag = os.environ.get("BUILD_NUMBER", "")
    if not tag.isdigit() or int(tag) < 1:
        raise ValueError("BUILD_NUMBER must be a positive integer")
    for variable in ("GITOPS_USERNAME", "GITOPS_TOKEN"):
        if not os.environ.get(variable):
            raise ValueError(f"Missing Jenkins credential variable: {variable}")

    source = Path(run("git", "rev-parse", "--show-toplevel", capture=True).stdout.strip()).resolve()
    source_commit = run("git", "rev-parse", "HEAD", cwd=source, capture=True).stdout.strip()
    tracked = run("git", "ls-files", "-z", "--", *PATHS, cwd=source, capture=True).stdout.split("\0")
    tracked = [name for name in tracked if name]
    if not tracked:
        raise ValueError("No tracked Kubernetes manifests found")
    for name in tracked:
        file = source / name
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(source):
            raise ValueError(f"Unexpected manifest file: {name}")

    with tempfile.TemporaryDirectory(prefix="gym-local-gitops-") as directory:
        temp = Path(directory)
        helper = temp / "askpass.sh"
        # The file contains variable names only, never credential values.
        helper.write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '  *Username*) printf "%s\\n" "$GITOPS_USERNAME" ;;\n'
            '  *Password*) printf "%s\\n" "$GITOPS_TOKEN" ;;\n'
            '  *) exit 1 ;;\nesac\n', encoding="utf-8",
        )
        helper.chmod(0o700)
        git_env = os.environ.copy()
        git_env.update(GIT_ASKPASS=str(helper), GIT_TERMINAL_PROMPT="0")
        checkout = temp / "repo"
        run("git", "-c", "credential.helper=", "clone", "--single-branch",
            "--branch", BRANCH, REPOSITORY, str(checkout), env=git_env)

        # Replace only the two managed manifest directories inside the fresh clone.
        # Keep branch history and all unrelated files. No force push.
        run("git", "rm", "-r", "--ignore-unmatch", "--", *PATHS, cwd=checkout)
        for name in tracked:
            target = checkout / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)

        kustomization = checkout / "infra/kubernetes/overlays/local/kustomization.yaml"
        config = yaml.safe_load(kustomization.read_text(encoding="utf-8"))
        config = update_images(config, tag)
        kustomization.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

        kubectl = source / ".ci-tools/kubectl"
        if not kubectl.is_file():
            raise ValueError("kubectl is missing; run the configuration scan stage first")
        rendered = run(str(kubectl), "kustomize", "infra/kubernetes/overlays/local",
                       cwd=checkout, capture=True).stdout
        # Check that all app and init-container image references use this build.
        found = set()
        for document in yaml.safe_load_all(rendered):
            if not isinstance(document, dict) or document.get("kind") != "Deployment":
                continue
            pod = document.get("spec", {}).get("template", {}).get("spec", {})
            for container in pod.get("containers", []) + pod.get("initContainers", []):
                image = container.get("image", "")
                for service in SERVICES:
                    if image.startswith(f"gym-lmf/{service}:"):
                        if image != f"gym-lmf/{service}:{tag}":
                            raise ValueError(f"Unexpected rendered image: {image}")
                        found.add(service)
        if found != set(SERVICES):
            raise ValueError("Not all three services were found in rendered manifests")

        run("git", "add", "--all", "--", *PATHS, cwd=checkout)
        diff = subprocess.run(("git", "diff", "--cached", "--quiet"), cwd=checkout)
        if diff.returncode == 0:
            print("Deployment manifests already match this build")
            return
        if diff.returncode != 1:
            raise RuntimeError("Could not inspect staged deployment changes")
        run("git", "-c", "user.name=Gym-LMF CI",
            "-c", "user.email=gym-lmf-ci@users.noreply.github.com",
            "commit", "-m", f"deploy(local): publish build {tag}",
            "-m", f"Source-Commit: {source_commit}", cwd=checkout)
        run("git", "-c", "credential.helper=", "push", "origin",
            f"HEAD:refs/heads/{BRANCH}", cwd=checkout, env=git_env)
        print(f"Published build {tag} to {BRANCH}; Argo sync is separate")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Local GitOps publication failed: {exc}", file=sys.stderr)
        sys.exit(1)
