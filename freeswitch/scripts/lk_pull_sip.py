#!/usr/bin/env python3
"""Extract the livekit-sip binary from the Docker Hub image without Docker."""
import json
import tarfile
import urllib.request

REPO = "livekit/sip"
OUT = "/opt/dialflow/livekit/livekit-sip"


def get(url, headers=None, raw=False):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    return data if raw else json.loads(data)


tok = get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{REPO}:pull")["token"]
H = {
    "Authorization": f"Bearer {tok}",
    "Accept": ", ".join([
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
    ]),
}

man = get(f"https://registry-1.docker.io/v2/{REPO}/manifests/latest", H)
if "manifests" in man:  # multi-arch index -> pick linux/amd64
    digest = next(
        m["digest"] for m in man["manifests"]
        if m.get("platform", {}).get("architecture") == "amd64"
        and m.get("platform", {}).get("os") == "linux"
    )
    man = get(f"https://registry-1.docker.io/v2/{REPO}/manifests/{digest}", H)

layers = man["layers"]
print(f"image has {len(layers)} layers")

found = False
for i, layer in enumerate(reversed(layers)):  # binary is in a top layer
    dg = layer["digest"]
    print(f"layer {i}: {dg[:24]}... ({layer.get('size', 0)//1024//1024} MB)")
    blob = get(f"https://registry-1.docker.io/v2/{REPO}/blobs/{dg}", {"Authorization": f"Bearer {tok}"}, raw=True)
    with open("/tmp/layer.tgz", "wb") as f:
        f.write(blob)
    with tarfile.open("/tmp/layer.tgz", "r:*") as t:
        for m in t.getmembers():
            if m.isfile() and m.name.split("/")[-1] == "livekit-sip":
                print("FOUND:", m.name, f"{m.size//1024//1024} MB")
                src = t.extractfile(m)
                with open(OUT, "wb") as out:
                    out.write(src.read())
                found = True
                break
    if found:
        break

if found:
    import os
    os.chmod(OUT, 0o755)
    print("extracted ->", OUT)
else:
    print("NOT FOUND in any layer")
