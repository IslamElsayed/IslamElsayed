#!/usr/bin/env python3
"""Rewrites the contributions section of README.md from GitHub search.

Lists pull requests by USER that were merged into public repositories the
user doesn't own, newest first.
"""
import json
import os
import re
import urllib.parse
import urllib.request

USER = os.environ.get("GITHUB_USER", "IslamElsayed")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
START, END = "<!-- contributions:start -->", "<!-- contributions:end -->"


def search(query):
    items, page = [], 1
    while True:
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "per_page": 100, "page": page, "sort": "created", "order": "desc"}
        )
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if TOKEN:
            request.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(request) as response:
            batch = json.load(response)["items"]
        items += batch
        if len(batch) < 100:
            return items
        page += 1


def repo_of(item):
    return item["repository_url"].split("/repos/", 1)[1]


def project(repo):
    owner, name = repo.split("/")
    # puma/puma, caddyserver/caddy and the like read better as just the name.
    return name if owner.lower().startswith(name.lower()) else repo


def clean_title(title):
    # Drop commit-style prefixes such as "fix(s3): " or "reverseproxy: ".
    title = re.sub(r"^[\w./()-]+:\s+", "", title)
    return title[:1].upper() + title[1:]


def render(merged):
    lines = []
    for pr in sorted(merged, key=lambda p: p["closed_at"], reverse=True):
        lines.append(f"- **{project(repo_of(pr))}**: [{clean_title(pr['title'])}]({pr['html_url']})")
    return "\n".join(lines)


def main():
    merged = search(f"is:pr is:public is:merged author:{USER} -user:{USER}")

    with open(README) as file:
        readme = file.read()
    section = f"{START}\n{render(merged)}\n{END}"
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: section, readme, flags=re.S)
    if updated != readme:
        with open(README, "w") as file:
            file.write(updated)


if __name__ == "__main__":
    main()
