#!/usr/bin/env python3
"""Extract libopusfile + libogg shared libs from the livekit/sip image."""
import json
import os
import tarfile
import urllib.request

REPO = "livekit/sip"
LIBDIR = "/opt/dialflow/livekit/lib"
WANT = ("libopusfile.so", "libogg.so", "libopusurl.so")


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
if "manifests" in man:
    digest = next(m["digest"] for m in man["manifests"]
                  if m.get("platform", {}).get("architecture") == "amd64"
                  and m.get("platform", {}).get("os") == "linux")
    man = get(f"https://registry-1.docker.io/v2/{REPO}/manifests/{digest}", H)

os.makedirs(LIBDIR, exist_ok=True)
got = []
for layer in man["layers"]:
    blob = get(f"https://registry-1.docker.io/v2/{REPO}/blobs/{layer['digest']}",
               {"Authorization": f"Bearer {tok}"}, raw=True)
    with open("/tmp/layer.tgz", "wb") as f:
        f.write(blob)
    with tarfile.open("/tmp/layer.tgz", "r:*") as t:
        for m in t.getmembers():
            base = m.name.split("/")[-1]
            if any(base.startswith(w) for w in WANT) and (m.isfile() or m.issym()):
                if m.issym():
                    # store symlink target name; recreate as copy of target later
                    print("symlink:", m.name, "->", m.linkname)
                    continue
                src = t.extractfile(m)
                dest = os.path.join(LIBDIR, base)
                with open(dest, "wb") as out:
                    out.write(src.read())
                got.append(base)
                print("extracted:", base)

# create .so.0 style names if only fully-versioned files came out
for f in os.listdir(LIBDIR):
    for w in WANT:
        short = w + ".0"
        if f.startswith(short + ".") and not os.path.exists(os.path.join(LIBDIR, short)):
            os.link(os.path.join(LIBDIR, f), os.path.join(LIBDIR, short))
            print("linked:", short, "->", f)
print("done:", sorted(os.listdir(LIBDIR)))
