# Development workshop

`dev.yaml` is a [Workshop](https://ubuntu.com/workshop) with
[OpenCode](https://opencode.ai), the GitHub CLI (`gh`), `uv`
and the build tools needed to run this project's checks.

```bash
workshop launch dev
workshop shell dev
```

Your OpenCode and `gh` logins and configuration are kept across
`workshop refresh` and `stop`/`start`, but `workshop remove` deletes them.

## Run checks

```bash
workshop run dev check        # lint, unit, static and coverage, like `tox`
workshop run dev unit -k foo  # extra arguments go to pytest
workshop run dev lint         # also: fmt, static
workshop run dev tox -e unit  # any tox command
```

Integration tests aren't supported in the workshop.

## Log in to OpenCode

Either copy your credentials from the host:

```bash
opencode auth export | workshop exec dev -- opencode auth import
```

Or log in inside the workshop
(GitHub Copilot shows a URL and code to open on the host):

```bash
workshop exec dev -- opencode auth login
```

The import skips credentials that already exist.
To update a rotated key, run `workshop exec dev -- opencode auth logout` first.

Choose your model with `/models` in OpenCode.
The project's `opencode.json` turns off OpenCode's own free models
and session sharing, so only the providers you log in to are used.

## Log in to GitHub

So that OpenCode can use `gh`, for example to read private repositories,
copy your host login:

```bash
gh auth token | workshop exec dev -- gh auth login --with-token
```

Or run `workshop exec dev -- gh auth login`.

The token gives OpenCode the same access as you, including push.
For less access, log in with a
[fine-grained token](https://github.com/settings/personal-access-tokens) instead.

## Sign commits

Commits in the workshop are signed with the SSH key of your host SSH agent.
Add that key on GitHub as a **Signing key** (Settings → SSH and GPG keys),
then set your Git identity once.
Use your GitHub email, or GitHub shows commits as unverified:

```bash
workshop exec dev -- git config --global user.name "Your Name"
workshop exec dev -- git config --global user.email you@example.com
```

Connect your SSH agent once after `workshop launch`
(it stays connected across `refresh` and `stop`/`start`):

```bash
workshop connect dev/git:ssh-agent
```

While it's connected, anything in the workshop, including OpenCode,
can use your SSH key. Disconnect it with
`workshop disconnect dev/git:ssh-agent`, or commit on the host instead.
To commit without signing, use `git commit --no-gpg-sign`.

## Optional: share OpenCode configuration with the host

To use the same skills, agents, commands, `AGENTS.md` and `opencode.json`
(including your default `model`) as on the host:

```bash
workshop stop dev
workshop remount dev/opencode:opencode-config ~/.config/opencode
workshop start dev
```

> [!WARNING]
> The workshop can then change your host OpenCode configuration,
> including plugins that the host runs.

To undo it:

```bash
workshop disconnect dev/opencode:opencode-config --forget
workshop connect dev/opencode:opencode-config :mount
```

Credentials and sessions aren't shared,
because the host and the workshop may run incompatible OpenCode versions.
