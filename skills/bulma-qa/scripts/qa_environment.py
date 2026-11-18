"""Resolve and launch pinned QA revisions with a host-owned local container profile."""

from base64 import b64decode
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
from uuid import uuid4


REPOSITORY = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
PR_URL = re.compile(rf"https://github\.com/({REPOSITORY})/pull/([1-9]\d*)")
OID = re.compile(r"[0-9a-f]{40}")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}")
SERVICE = re.compile(r"[a-z][a-z0-9-]{0,31}")
BRANCH = re.compile(r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,180}")
GATEWAY_MODE = "com.docker.network.bridge.gateway_mode_ipv4"
DEPENDENCY = re.compile(
    r"^\s*(?:[-*]\s+)?(?:\*\*)?(?:QA[- ]Dependenc(?:y|ies)|Depends on|Requires|"
    r"(?:Frontend|Backend|API(?: V2)?|UI) (?:PR|branch|commit|dependency))"
    r"(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.*?)\s*$", re.I | re.M,
)


class Blocked(RuntimeError):
    pass


@dataclass(frozen=True)
class Revision:
    repository: str
    ref: str
    oid: str


def run(argv, *, timeout=25):
    try:
        return subprocess.check_output(argv, stderr=subprocess.DEVNULL, text=True, timeout=timeout).strip()
    except (OSError, subprocess.SubprocessError):
        raise Blocked(f"The trusted QA host could not complete {argv[0]} {argv[1]}.") from None


def read_pr(url, command=run, *, companion=False):
    match = PR_URL.fullmatch(url)
    if not match:
        raise Blocked("The QA request needs an exact pull request URL.")
    repository, number = match.groups()
    data = json.loads(command(["gh", "pr", "view", url, "--json", "url,state,headRefOid,body"]))
    states = {"OPEN", "MERGED"} if companion else {"OPEN"}
    if (data.get("url", "").casefold() != url.casefold() or data.get("state") not in states
            or not OID.fullmatch(data.get("headRefOid") or "")):
        raise Blocked("The requested open PR and its current head could not be verified.")
    return Revision(repository, f"refs/pull/{number}/head", data["headRefOid"]), data.get("body") or ""


def declared_dependencies(body, repository):
    declarations = []
    for line in DEPENDENCY.findall(body):
        text = line.strip().strip("`")
        if text.casefold() in {"none", "n/a", "not applicable"}:
            continue
        # Match the repositories' documented Requires/QA dependencies lists.
        links = re.findall(rf"{PR_URL.pattern}(?=$|[\s,>)])|(?<![\w/])#([1-9][0-9]*)\b", text)
        if links:
            declarations.extend((repo or repository, f"https://github.com/{repo or repository}/pull/{num or local}")
                                for repo, num, local in links)
            continue
        parts = text.split()
        if len(parts) != 2 or not re.fullmatch(REPOSITORY, parts[0]) or not valid_ref(parts[1]):
            raise Blocked("A QA dependency is declared but lacks an exact PR, repository ref, or commit.")
        declarations.append(tuple(parts))
    return declarations


def valid_ref(ref):
    return bool(OID.fullmatch(ref) or (
        BRANCH.fullmatch(ref) and ".." not in ref and "//" not in ref
        and all(part and not part.endswith((".", ".lock")) for part in ref.split("/"))
    ))


def remote_for(repository, source, command):
    checkout = Path(source).resolve(strict=True)
    origin = command(["git", "-C", str(checkout), "remote", "get-url", "origin"])
    allowed = {f"https://github.com/{repository}", f"git@github.com:{repository}",
               f"ssh://git@github.com/{repository}"}
    if origin.removesuffix(".git").casefold() not in {url.casefold() for url in allowed}:
        raise Blocked("The approved checkout does not match its configured repository.")
    return origin


def pin_ref(repository, ref, component, command):
    if not valid_ref(ref):
        raise Blocked("No exact compatible base is configured for a required QA component.")
    if OID.fullmatch(ref):
        return Revision(repository, ref, ref)
    remote = remote_for(repository, component["checkout"], command)
    matches = command(["git", "ls-remote", "--exit-code", remote, ref]).splitlines()
    if len(matches) != 1:
        raise Blocked("A configured QA reference does not identify one remote commit.")
    oid, observed = matches[0].split()
    if observed != ref or not OID.fullmatch(oid):
        raise Blocked("A configured QA reference could not be resolved.")
    return Revision(repository, ref, oid)


def resolve_revisions(profile, pr, command=run):
    components = {item["repo"].casefold(): item for item in profile["services"].values() if item.get("repo")}
    main, body = read_pr(pr, command)
    primary = main.repository.casefold()
    if primary not in components:
        raise Blocked("The PR repository is outside the approved QA profile.")
    verified = {pr.casefold(): main}
    sources = declared_dependencies(body, main.repository) + list(
        profile.get("dependencies", {}).get(main.oid, {}).items(),
    )
    pins = {primary: main}
    for repository, ref in sources:
        if len(sources) > 12:
            raise Blocked("The QA dependency declarations exceed the profile resolution limit.")
        key = repository.casefold()
        if key not in components:
            raise Blocked("A declared dependency is outside the approved QA profile.")
        matched = PR_URL.fullmatch(ref)
        if matched:
            if matched[1].casefold() != key:
                raise Blocked("A QA dependency PR does not match its declared repository.")
            revision = verified.get(ref.casefold())
            if revision is None:
                revision, companion_body = read_pr(ref, command, companion=True)
                verified[ref.casefold()] = revision
                sources.extend(declared_dependencies(companion_body, revision.repository))
                sources.extend(profile.get("dependencies", {}).get(revision.oid, {}).items())
        else:
            revision = pin_ref(repository, ref, components[key], command)
        old = pins.get(key)
        if old and old.oid != revision.oid:
            raise Blocked(f"QA dependency evidence conflicts for {repository}.")
        pins.setdefault(key, revision)
    return {name: pins.get(item["repo"].casefold()) or
            pin_ref(item["repo"], item.get("base_ref", ""), item, command)
            for name, item in profile["services"].items() if item.get("repo")}


def checkout_revision(directory, revision, component, command=run):
    remote = remote_for(revision.repository, component["checkout"], command)
    gitdir = directory / "git"
    worktree = directory / "worktree"
    directory.mkdir()
    command(["git", "init", "--bare", str(gitdir)])
    git = ["git", "--git-dir", str(gitdir), "-c", "core.hooksPath=/dev/null"]
    command([*git, "fetch", "--no-tags", "--depth=1", remote, revision.ref], timeout=120)
    if command([*git, "rev-parse", "FETCH_HEAD"]) != revision.oid:
        raise Blocked("A QA revision changed during checkout. Request the current head.")
    # Keep local hooks and checkout filters from interpreting PR-controlled attributes.
    isolated_git = ["env", "GIT_CONFIG_NOSYSTEM=1", "GIT_CONFIG_GLOBAL=/dev/null", *git]
    command([*isolated_git, "worktree", "add", "--detach", "--no-checkout", str(worktree), revision.oid], timeout=60)
    # Export only tracked files to the guest. The checkout's Git metadata stays on the host.
    guest = directory / "source"
    guest.mkdir()
    archive = directory / "source.tar"
    command([*isolated_git, "archive", "--format=tar", "-o", str(archive), revision.oid], timeout=60)
    with tarfile.open(archive) as source:
        if not hasattr(tarfile, "data_filter"):
            raise Blocked("QA provisioning needs a Python version with safe tar extraction.")
        source.extractall(guest, filter=runtime_source)
    return guest


def runtime_source(member, destination):
    parts = Path(member.name).parts
    credential_files = {".aws", ".docker", ".git", ".gitconfig", ".gnupg", ".netrc",
                        ".local-db", ".npmrc", ".pypirc", ".ssh"}
    if any(part in credential_files or part.startswith(".env") for part in parts):
        return None
    return tarfile.data_filter(member, destination)


def environment_hash(profile, revisions):
    data = {"services": profile["services"], "browser": profile["browser"], "runtime": 1,
            "payment_mode": profile["payment_mode"], "revisions": {n: r.oid for n, r in revisions.items()}}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def validate_profile(profile):
    services = profile["services"]
    if (not services or len(services) > 6 or profile["browser"] not in services
            or not IMAGE.fullmatch(profile["browser_image"])):
        raise Blocked("The approved QA runtime needs a browser service and bounded dependencies.")
    if profile.get("payment_mode") not in {"stub", "disabled"} or profile.get("synthetic_identity") is not True:
        raise Blocked("Provisioned QA requires a synthetic test identity and disabled or stubbed payments.")
    repositories = [service["repo"].casefold() for service in services.values() if service.get("repo")]
    if not repositories or len(set(repositories)) != len(repositories):
        raise Blocked("The approved QA runtime must map each repository to one service.")
    for name, service in services.items():
        if (not SERVICE.fullmatch(name) or not IMAGE.fullmatch(service["image"])
                or (service.get("repo") and not re.fullmatch(REPOSITORY, service["repo"]))
                or not isinstance(service["start"], list) or not service["start"]
                or not all(isinstance(word, str) and word and "\x00" not in word for word in service["start"])
                or not isinstance(service["port"], int) or not 1024 <= service["port"] <= 65535
                or not re.fullmatch(r"/[A-Za-z0-9/_-]*", service["ready_path"])):
            raise Blocked("The approved QA service profile is incomplete or unsafe.")


def inspect_stack(names, profile, revisions, wanted, docker):
    if set(names) != set(profile["services"]):
        raise Blocked("The reusable QA stack does not contain every required service.")
    network = None
    members = set()
    for service, name in names.items():
        cfg = profile["services"][service]
        if not re.fullmatch(r"bulma-qa-[a-zA-Z0-9_-]+", name):
            raise Blocked("The reusable container is not part of a trusted QA stack.")
        obj = json.loads(docker("inspect", "--type", "container", name))[0]
        revision = revisions[service].oid if service in revisions else "fixture"
        labels = obj["Config"]["Labels"] or {}
        host = obj["HostConfig"]
        mounts = obj["Mounts"]
        if (not obj["State"]["Running"] or labels.get("bulma.qa.profile") != wanted
                or labels.get("bulma.qa.revision") != revision or obj["Image"] != cfg["image"]
                or host["Privileged"] or not host["ReadonlyRootfs"]
                or obj["Config"]["User"] != "65532:65532"
                or host.get("CapDrop") != ["ALL"] or host.get("CapAdd")
                or host.get("PidMode") == "host" or host.get("IpcMode") == "host"
                or host.get("Devices") or host.get("DeviceRequests") or host.get("VolumesFrom")
                or host.get("Dns") != ["127.0.0.1"] or host.get("ExtraHosts")
                or host.get("PublishAllPorts") or host.get("PortBindings")
                or "no-new-privileges" not in (host.get("SecurityOpt") or [])
                or len(mounts) != int(service in revisions)
                or any(item["Type"] != "bind" or item["Destination"] != "/source" or item["RW"] for item in mounts)
                or obj["Config"]["Cmd"] != cfg["start"]):
            raise Blocked("The QA instance does not match the approved runtime or pinned revisions.")
        networks = obj["NetworkSettings"]["Networks"]
        if len(networks) != 1 or any(obj["NetworkSettings"]["Ports"].values()):
            raise Blocked("A QA service has an unapproved network attachment.")
        current = next(iter(networks))
        if network is not None and network != current:
            raise Blocked("The QA services do not share one isolated network.")
        network = current
        if service not in (networks[current].get("Aliases") or []):
            raise Blocked("A QA service is missing its approved network name.")
        members.add(obj["Id"])
    info = json.loads(docker("network", "inspect", network))[0]
    if (not network.startswith("bulma-qa-") or not info["Internal"] or info["Driver"] != "bridge"
            or info["EnableIPv6"] or info["Options"].get(GATEWAY_MODE) != "isolated"
            or set(info["Containers"]) != members):
        raise Blocked("The QA network does not isolate services from external resources.")
    return network


def wait_ready(execute, profile, *, timeout=30):
    waiting = set(profile["services"])
    deadline = time.monotonic() + timeout
    while waiting and time.monotonic() < deadline:
        for service in list(waiting):
            cfg = profile["services"][service]
            try:
                status = execute("curl", "--noproxy", "*", "--max-time", "2", "--silent",
                                 "--output", "/dev/null", "--write-out", "%{http_code}",
                                 f"http://{service}:{cfg['port']}{cfg['ready_path']}")
                if re.fullmatch(r"2\d\d", status):
                    waiting.remove(service)
            except (OSError, Blocked, subprocess.SubprocessError):
                continue
        if waiting:
            time.sleep(.3)
    if waiting:
        raise Blocked("The isolated QA services did not become ready: " + ", ".join(sorted(waiting)) + ".")


def local_engine(command=run):
    endpoint = os.environ.get("DOCKER_HOST") or command(
        ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
    )
    if not endpoint.startswith("unix:///") or not Path(endpoint.removeprefix("unix://")).is_socket():
        raise Blocked("QA provisioning requires a local Docker socket.")

    def docker(*argv, timeout=25):
        return command(["docker", "--host", endpoint, *argv], timeout=timeout)

    return docker


def remove_owned(docker, kind, name):
    try:
        if kind == "network":
            docker("network", "rm", name, timeout=5)
        else:
            docker("rm", "-fv", name, timeout=5)
    except Blocked:
        # The resource may never have been created if startup failed.
        ls = ["network", "ls"] if kind == "network" else ["container", "ls", "--all"]
        name_filter = f"name=^{name}$" if kind == "network" else f"name=^/{name}$"
        listed = docker(*ls, "--quiet", "--filter", name_filter, timeout=5)
        if listed:
            raise Blocked("An owned QA resource could not be cleaned up.") from None


def container_args(network, name):
    return ["run", "--detach", "--pull=never", "--name", name, "--network", network,
            "--read-only", "--user", "65532:65532", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "192", "--memory", "1g", "--init", "--dns", "127.0.0.1",
            "--tmpfs", "/tmp:rw,nosuid,nodev,mode=1777", "--tmpfs", "/work:rw,nosuid,nodev,mode=1777",
            "--workdir", "/work", "--env", "HOME=/work"]


@dataclass(frozen=True)
class Browser:
    docker: object
    name: str
    url: str
    reused: bool

    def run(self, *argv):
        return self.docker("exec", self.name, *argv)

    def capture(self, selector, path, *base):
        self.run(*base, "screenshot", selector, "/work/proof.png")
        size = int(self.run("stat", "-c", "%s", "/work/proof.png"))
        if not 0 < size <= 8_000_000:
            raise Blocked("The screenshot could not be cleared as evidence.")
        # Base64 keeps the host command transport text-only.
        path.write_bytes(b64decode(self.run("base64", "/work/proof.png")))
        return self.run("tesseract", "/work/proof.png", "stdout")


@contextmanager
def open_browser(docker, profile, network, *, reused):
    name = f"bulma-qa-{uuid4().hex[:12]}-browser"
    service = profile["browser"]
    url = f"http://{service}:{profile['services'][service]['port']}"
    browser = Browser(docker, name, url, reused)
    with ExitStack() as cleanup:
        cleanup.callback(remove_owned, docker, "container", name)
        docker(*container_args(network, name), "--entrypoint", "/bin/sleep", profile["browser_image"], "infinity")
        obj = json.loads(docker("inspect", "--type", "container", name))[0]
        if (obj["Mounts"] or set(obj["NetworkSettings"]["Networks"]) != {network}
                or obj["Image"] != profile["browser_image"]):
            raise Blocked("The trusted browser image has an unexpected mount or network.")
        yield browser


@contextmanager
def provision(profile, revisions, directory, command=run):
    validate_profile(profile)
    docker = local_engine(command)
    images = {cfg["image"] for cfg in profile["services"].values()} | {profile["browser_image"]}
    for image in sorted(images):
        info = json.loads(docker("image", "inspect", image))[0]
        if info["Id"] != image or info["Config"].get("Volumes"):
            raise Blocked("A pinned QA image has undeclared storage or could not be verified.")
    wanted = environment_hash(profile, revisions)
    reuse = profile.get("reuse", {})
    if reuse:
        try:
            network = inspect_stack(reuse, profile, revisions, wanted, docker)
        except Blocked:
            pass
        else:
            with open_browser(docker, profile, network, reused=True) as browser:
                try:
                    wait_ready(browser.run, profile, timeout=4)
                except Blocked:
                    pass
                else:
                    yield browser
                    return
    token = uuid4().hex[:12]
    network = f"bulma-qa-{token}"
    names = {}

    with ExitStack() as cleanup:
        cleanup.callback(remove_owned, docker, "network", network)
        docker("network", "create", "--internal", "--opt", f"{GATEWAY_MODE}=isolated", network)
        for name, cfg in profile["services"].items():
            container = f"bulma-qa-{token}-{name}"
            revision = revisions.get(name)
            argv = [*container_args(network, container), "--network-alias", name,
                    "--label", f"bulma.qa.profile={wanted}",
                    "--label", f"bulma.qa.revision={revision.oid if revision else 'fixture'}"]
            if revision:
                guest = checkout_revision(directory / name, revision, cfg, command)
                if "," in str(guest):
                    raise Blocked("The isolated checkout path cannot be mounted safely.")
                argv.extend(["--mount", f"type=bind,src={guest},dst=/source,readonly"])
            cleanup.callback(remove_owned, docker, "container", container)
            docker(*argv, cfg["image"], *cfg["start"], timeout=45)
            names[name] = container
        inspect_stack(names, profile, revisions, wanted, docker)
        with open_browser(docker, profile, network, reused=False) as browser:
            wait_ready(browser.run, profile)
            yield browser
