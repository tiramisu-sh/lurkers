# docs

`lurkers.mdx` is the source for the **lurkers** page on the docs site —
[tiramisu.sh/docs/lurkers](https://tiramisu.sh/docs/lurkers). The
[website](https://github.com/tiramisu-sh/website) pulls this file at build
time, so edit it here — not in the website repo.

## Preview locally

In a checkout of the website repo, point its dev server at this folder:

```bash
LURKERS_DOCS_PATH=/abs/path/to/lurkers/docs bun run dev
```

That renders this file — uncommitted edits included — with the site's styling.
Without the env var the site fetches the published version from `main`.
