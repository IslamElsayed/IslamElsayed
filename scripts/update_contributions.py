#!/usr/bin/env python3
"""Rewrites the contributions section of README.md from GitHub search.

Lists pull requests by USER that were merged into public repositories the
user doesn't own, grouped by project. Projects are ordered by their latest
merge, and each project's pull requests newest first.
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


# How a project is shown; anything not listed is shown by its repository name.
DISPLAY_NAMES = {
    "puma/puma": "Puma",
    "caddyserver/caddy": "Caddy",
    "caddyserver/website": "Caddy docs",
    "ruby/rubygems": "RubyGems",
    "rubygems/rubygems": "RubyGems",
    "grafana/k6": "k6",
    "supabase/storage": "Supabase Storage",
    "solidusio/solidus": "Solidus",
    "spree/spree": "Spree",
    "traefik/traefik": "Traefik",
    "derailed/k9s": "k9s",
    "rails/solid_queue": "Solid Queue",
    "thoughtbot/factory_bot": "factory_bot",
    "rubocop/rubocop": "RuboCop",
    "rubocop/rubocop-rails": "RuboCop Rails",
}


def project(repo):
    return DISPLAY_NAMES.get(repo, repo.split("/")[1])


def clean_title(title):
    # Drop commit-style prefixes such as "fix(s3): " or "reverseproxy: ".
    title = re.sub(r"^[\w./()-]+:\s+", "", title)
    return title[:1].upper() + title[1:]


def link(pr):
    return f"[{clean_title(pr['title'])}]({pr['html_url']})"


def render(merged):
    groups = {}
    for pr in sorted(merged, key=lambda p: p["closed_at"], reverse=True):
        groups.setdefault(project(repo_of(pr)), []).append(pr)

    lines = []
    for name, prs in groups.items():
        if len(prs) == 1:
            lines.append(f"- **{name}**: {link(prs[0])}")
        else:
            lines.append(f"- **{name}**")
            lines.extend(f"  - {link(pr)}" for pr in prs)
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
