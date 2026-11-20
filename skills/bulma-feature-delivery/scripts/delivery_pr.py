"""Create or recover a ready GitHub pull request on an exact head and base."""

import argparse
import json
import re
import subprocess
import sys


POSITION = re.compile(r"^\[(?:First|Second|Third|[0-9]+ of [0-9]+|Final / Umbrella)\] ")


def gh(*args):
    return subprocess.run(["gh", *args], check=True, text=True, stdout=subprocess.PIPE).stdout


def pull_for_head(repo, head):
    owner = repo.split("/")[0]
    pages = json.loads(gh(
        "api", "--method", "GET", f"repos/{repo}/pulls", "--paginate", "--slurp",
        "-f", f"head={owner}:{head}", "-f", "state=all",
    ))
    pulls = [pr for page in pages for pr in page
             if pr["head"]["ref"] == head
             and (pr["head"]["repo"] or {}).get("full_name", "").casefold() == repo.casefold()]
    if len(pulls) > 1:
        raise ValueError(f"Multiple pull requests found for {head}; reconcile the branch before continuing.")
    if not pulls:
        return None
    # The individual endpoint includes the authoritative merged flag and merge commit.
    return json.loads(gh("api", f"repos/{repo}/pulls/{pulls[0]['number']}"))


def check_base(pr, repo, base):
    if (pr["base"]["repo"]["full_name"].casefold(), pr["base"]["ref"]) != (repo.casefold(), base):
        raise ValueError(f"Base drift on {pr['html_url']}: expected {repo}:{base}, "
                         f"found {pr['base']['repo']['full_name']}:{pr['base']['ref']}.")
    if pr["state"] != "open" and not pr["merged"]:
        raise ValueError(f"Pull request {pr['html_url']} was closed without merging.")


def positioned(title, position):
    return f"[{position}] {POSITION.sub('', title)}" if position else title


def ensure(repo, head, base, title, body_file, assignee, position=None):
    pr = pull_for_head(repo, head)
    if pr is None:
        args = ["pr", "create", "--repo", repo, "--head", head, "--base", base,
                "--title", positioned(title, position), "--body-file", body_file]
        if assignee:
            args.extend(["--assignee", assignee])
        gh(*args)
        pr = pull_for_head(repo, head)
        if pr is None:
            raise ValueError(f"Created pull request could not be read back for {head}.")
        if pr["draft"]:
            raise ValueError(f"New pull request is unexpectedly draft: {pr['html_url']}.")
    else:
        check_base(pr, repo, base)
        if pr["state"] == "open" and positioned(pr["title"], position) != pr["title"]:
            gh("pr", "edit", pr["html_url"], "--title", positioned(pr["title"], position))
            pr = pull_for_head(repo, head)
            if pr is None or positioned(pr["title"], position) != pr["title"]:
                raise ValueError(f"Could not verify the title position for {head}.")
    check_base(pr, repo, base)
    return {"url": pr["html_url"], "head_sha": pr["head"]["sha"], "draft": pr["draft"],
            "state": "merged" if pr["merged"] else pr["state"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "head", "base", "title", "body-file"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--assignee")
    parser.add_argument("--position")
    try:
        print(json.dumps(ensure(**vars(parser.parse_args()))))
    except (KeyError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
