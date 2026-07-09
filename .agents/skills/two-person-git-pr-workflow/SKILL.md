---
name: two-person-git-pr-workflow
description: Fork-based Git and PR workflow for a two-person collaboration where EmiliaTQAQ manages the upstream repository and the contributor works from a personal fork. Use when Codex needs to reduce Git conflicts, prepare commits, create/update PRs, sync fork main after upstream merges, choose merge/rebase commands, or explain contributor versus maintainer responsibilities.
---

# Two-Person Git PR Workflow

Use this skill to keep the fork workflow clean:

- EmiliaTQAQ owns and merges the upstream `main`.
- The contributor works in a fork (`origin`) and sends PRs to upstream.
- Local `main` is a sync branch only. Do feature work on topic branches.
- Resolve PR conflicts in the contributor branch before maintainer merge.

## First Checks

Before giving Git commands or editing anything, inspect:

```powershell
git status -sb
git remote -v
git branch --show-current
```

Expected remote shape:

```text
origin   <contributor fork URL>
upstream https://github.com/EmiliaTQAQ/kaiwu.git
```

If `upstream` is missing, add it once:

```powershell
git remote add upstream https://github.com/EmiliaTQAQ/kaiwu.git
git fetch upstream
```

If the repository name or owner differs, confirm the upstream URL before adding it.

## Contributor Workflow

Keep `main` clean and synced:

```powershell
git switch main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
```

Start every task from the synced `main`:

```powershell
git switch main
git fetch upstream
git merge --ff-only upstream/main
git switch -c feat/short-task-name
```

Do the work, then commit by logical unit:

```powershell
git status -sb
git add <files>
git commit -m "feat(scope): short Chinese or English summary"
git push -u origin feat/short-task-name
```

Open the PR:

- base: `EmiliaTQAQ/kaiwu:main`
- compare: contributor fork `feat/short-task-name`
- title: match the main commit style
- body: include change summary, verification commands, and risk notes

## Commit Style

Use concise Conventional Commit style:

```text
feat(project-library): 增加图片预览
fix(config): 修复本地 API 代理
docs(trellis): 记录 PR 协作流程
chore(deps): 更新依赖
refactor(frontend): 拆分图片预览组件
```

Rules:

- Prefer one coherent change per commit.
- Do not commit unrelated generated files, caches, or local environment files.
- Do not use vague messages such as `update`, `fix bug`, `wip`.
- Keep PRs small: one feature, one bug fix, or one docs update.
- Avoid stacking multiple unrelated PRs on the same branch.

## Updating an Open PR

When upstream `main` changes while the PR is open, update the contributor branch:

```powershell
git fetch upstream
git switch feat/short-task-name
git rebase upstream/main
git push --force-with-lease origin feat/short-task-name
```

Use `--force-with-lease` only for the contributor's own feature branch, never for `main`.

If rebase is uncomfortable or the branch is shared, use merge instead:

```powershell
git fetch upstream
git switch feat/short-task-name
git merge upstream/main
git push origin feat/short-task-name
```

## Conflict Rules

To reduce conflicts:

- Sync from `upstream/main` before starting work.
- Keep PRs narrow and short-lived.
- Avoid direct feature work on `main`.
- Avoid editing broad files unless necessary, especially large app entry files, global CSS, config, generated previews, and task bookkeeping.
- Do not include unrelated `.trellis/tasks/*`, build output, image cache, or local `.env` changes in feature PRs.

When conflicts happen:

1. Resolve conflicts on the contributor branch, not on upstream `main`.
2. Prefer the branch's intended feature changes only where they are truly newer.
3. Keep unrelated upstream changes intact.
4. Run the relevant checks after resolving.
5. Push the same PR branch again.

## Maintainer Workflow

For EmiliaTQAQ as upstream maintainer:

1. Review the PR diff and scope.
2. Check CI/build output or ask contributor to run verification.
3. Request changes if the PR is too broad, includes unrelated files, or conflicts with upstream direction.
4. Merge only after conflicts are resolved and checks pass.
5. Prefer squash merge for small single-purpose PRs; use merge commit when preserving multiple meaningful commits matters.
6. Delete the merged feature branch if it is no longer needed.

The maintainer does not need to pull from the contributor's fork manually unless reviewing locally.

## After PR Is Merged

After EmiliaTQAQ merges the PR, sync the contributor fork:

```powershell
git switch main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
```

Then delete the local feature branch if no longer needed:

```powershell
git branch -d feat/short-task-name
git push origin --delete feat/short-task-name
```

If `git merge --ff-only upstream/main` fails, stop and inspect `git status -sb` plus `git log --oneline --left-right HEAD...upstream/main`. Do not force-push `main` unless the user explicitly confirms the consequence.

## Safety Rules

- Never push directly to `upstream main` from the contributor account.
- Never use `git reset --hard` or force-push `main` without explicit user confirmation.
- Never solve conflicts by blindly accepting one side across the whole repo when generated files or broad UI/backend changes are involved.
- Before committing, show unrecognized dirty files separately and exclude them unless the user confirms.
