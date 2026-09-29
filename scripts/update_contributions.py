#!/usr/bin/env python3
"""Rewrites the contributions section of README.md from GitHub search.

Lists pull requests by USER that were merged into (or are open against)
public repositories the user doesn't own.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from collections import defaultdict

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


def render(merged, open_prs):
    lines = []
    by_repo = defaultdict(list)
    for pr in merged:
        by_repo[repo_of(pr)].append(pr)

    lines.append(f"**{len(merged)} merged** into {len(by_repo)} projects · **{len(open_prs)} in review**\n")
    lines.append("### Merged\n")
    for repo, prs in sorted(by_repo.items(), key=lambda kv: max(p["closed_at"] for p in kv[1]), reverse=True):
        lines.append(f"**[{repo}](https://github.com/{repo})**")
        for pr in sorted(prs, key=lambda p: p["closed_at"], reverse=True):
            lines.append(f"- [{pr['title']}]({pr['html_url']}) · {pr['closed_at'][:10]}")
        lines.append("")

    if open_prs:
        lines.append("### In review\n")
        for pr in sorted(open_prs, key=lambda p: p["created_at"], reverse=True):
            lines.append(f"- [{repo_of(pr)}#{pr['number']}]({pr['html_url']}): {pr['title']}")
        lines.append("")

    return "\n".join(lines)


def main():
    base = f"is:pr is:public author:{USER} -user:{USER}"
    merged = search(f"{base} is:merged")
    open_prs = search(f"{base} is:open")

    with open(README) as file:
        readme = file.read()
    section = f"{START}\n{render(merged, open_prs)}\n{END}"
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: section, readme, flags=re.S)
    if updated != readme:
        with open(README, "w") as file:
            file.write(updated)


if __name__ == "__main__":
    main()
