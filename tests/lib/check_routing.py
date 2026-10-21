#!/usr/bin/env python3
"""Lexical routing check over skill descriptions. No network, no model.

A host picks a skill from its name and description. This approximates that
choice with stemmed TF-IDF so CI catches the two common trigger bugs:

- a description missing the words users say (a positive prompt in
  evals/routing/<skill>.json does not rank its skill in the top k), and
- an over-broad description (a negative prompt ranks the wrong skill first,
  or two descriptions are near-duplicates).

It cannot judge meaning. A failure here usually means fix the description,
not the case. evals/README.md covers the model-backed tier.
"""
import json
import math
import os
import re
import sys
from collections import Counter

from frontmatter import parse, skill_files

DEFAULT_TOP_K = 3
OWNER_TOP_K = 3
# Share of positive prompts that must rank their skill first. Ratchet: raise it
# when descriptions improve, never lower it to make a change pass.
MIN_RANK1 = 0.85
# Cosine similarity above which two descriptions compete for the same prompts.
MAX_SIMILARITY = 0.5
# Pairs that are the same skill under two names on purpose.
ALIASES = {frozenset({"bulma-fd", "bulma-feature-delivery"})}

STOP = set("""
a an and are as at be by for from has have i if in into is it its me my of on
or our so that the their then this to use used uses using via was we when
where which while who will with you your do does can should would could this
these those any all only not no it's what how one each per
""".split())


def stem(word):
    """Crude suffix strip. Enough to match review/reviews/reviewing/reviewer."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("sses", "xes", "ches", "shes")):
        word = word[:-2]
    elif word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        word = word[:-1]
    for suffix in ("ation", "ion", "ing", "er", "ed", "ly"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokens(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(w) for w in words if w not in STOP and len(w) > 1]


def load_skills(root):
    skills = {}
    for path in skill_files(root):
        fields, _ = parse(path)
        name = os.path.basename(os.path.dirname(path))
        # The name is part of what the host sees, and users type it.
        skills[name] = tokens(name.replace("-", " ") + " " + (fields or {}).get("description", ""))
    return skills


class Index:
    def __init__(self, docs):
        self.names = sorted(docs)
        df = Counter()
        for words in docs.values():
            df.update(set(words))
        n = len(docs)
        self.idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
        self.vectors = {name: self.vector(docs[name]) for name in self.names}

    def vector(self, words):
        counts = Counter(w for w in words if w in self.idf)
        vec = {w: (1 + math.log(c)) * self.idf[w] for w, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {w: v / norm for w, v in vec.items()}

    @staticmethod
    def cosine(a, b):
        return sum(v * b.get(w, 0.0) for w, v in a.items())

    def rank(self, prompt):
        query = self.vector(tokens(prompt))
        scored = [(self.cosine(query, self.vectors[n]), n) for n in self.names]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [name for score, name in scored if score > 0]


def position(ranking, name):
    return ranking.index(name) + 1 if name in ranking else None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    verbose = "--verbose" in sys.argv
    skills = load_skills(root)
    index = Index(skills)
    errors = []

    names = index.names
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            if frozenset({left, right}) in ALIASES:
                continue
            score = index.cosine(index.vectors[left], index.vectors[right])
            if score > MAX_SIMILARITY:
                errors.append(f"descriptions collide: {left} ~ {right} ({score:.2f} > {MAX_SIMILARITY})")

    case_dir = os.path.join(root, "evals", "routing")
    positives = rank1 = 0
    for filename in sorted(os.listdir(case_dir)):
        if not filename.endswith(".json"):
            continue
        rel = os.path.join("evals", "routing", filename)
        with open(os.path.join(case_dir, filename), encoding="utf-8") as handle:
            case = json.load(handle)
        skill = case.get("skill", "")
        if skill != filename[: -len(".json")]:
            errors.append(f"{rel}: skill {skill!r} does not match the file name")
            continue
        if skill not in skills:
            errors.append(f"{rel}: no such skill {skill!r}")
            continue
        if not case.get("positive") or not case.get("negative"):
            errors.append(f"{rel}: needs at least one positive and one negative prompt")
        for item in case.get("positive", []):
            ranking = index.rank(item["prompt"])
            top_k = item.get("top_k", DEFAULT_TOP_K)
            pos = position(ranking, skill)
            positives += 1
            rank1 += pos == 1
            if verbose:
                print(f"+ {skill} #{pos} {item['prompt']!r} top={ranking[:3]}")
            if pos is None or pos > top_k:
                errors.append(f"{rel}: {skill} ranks #{pos} (want top {top_k}) for "
                              f"{item['prompt']!r}; top 3: {ranking[:3]}")
        for item in case.get("negative", []):
            ranking = index.rank(item["prompt"])
            owner = item.get("owner")
            if verbose:
                print(f"- {skill} #{position(ranking, skill)} {item['prompt']!r} top={ranking[:3]}")
            if ranking[:1] == [skill]:
                errors.append(f"{rel}: {skill} ranks first for a prompt it must not take: "
                              f"{item['prompt']!r}")
            if owner:
                if owner not in skills:
                    errors.append(f"{rel}: owner {owner!r} is not a skill")
                    continue
                pos = position(ranking, owner)
                if pos is None or pos > OWNER_TOP_K:
                    errors.append(f"{rel}: owner {owner} ranks #{pos} (want top {OWNER_TOP_K}) "
                                  f"for {item['prompt']!r}; top 3: {ranking[:3]}")

    share = rank1 / positives if positives else 0.0
    print(f"routing: {rank1}/{positives} positive prompts rank their skill first ({share:.0%})")
    if positives and share < MIN_RANK1:
        errors.append(f"rank-1 share {share:.0%} is under the floor {MIN_RANK1:.0%}")

    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} routing problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
