# SSP Response Log

This file mirrors substantive project responses so the current guidance and code links are easy to copy from GitHub.

Publishing rules:

- Project decisions, notebook instructions, code links, and status updates are committed automatically.
- Executable code stays in dedicated source files and is linked from this log.
- Credentials, authentication data, and raw sensitive Archer records are never published because this repository is public.

## 2026-09-01 - Automatic publishing enabled

Automatic publishing is now active for the Archer-to-OSCAL SSP work.

### Current continuation point

The active target is `system-characteristics.props[]`.

The confirmed read-only notebook cells are available at:

- [`notebooks/ssp_props_read_only_cells.py`](notebooks/ssp_props_read_only_cells.py)

### Next action

1. Confirm `EXECUTE_WRITES = False`.
2. Run Cell 3, **count populated candidate prop fields across all SSPs**.
3. Paste only the output beginning with:

```text
=== POPULATED PROP FIELD COUNTS ===
```

Those counts determine which source fields need value-resolution rules and which can be excluded before the final OSCAL `props[]` transformation is designed.


## 2026-09-03 - Access this task from a phone

Yes. This Codex task can be continued from the ChatGPT mobile app using **Remote**.

Setup:

1. On the Windows computer, open the ChatGPT desktop app.
2. Go to **Settings > Connections > Control this Mac or PC**.
3. Select **Set up** or **Add** and approve remote access.
4. Scan the displayed QR code with the phone.
5. On the phone, sign in to the same ChatGPT account and workspace.
6. In the ChatGPT mobile app, open **Remote**, choose the connected computer, and select this task.

The computer must remain awake, online, and running the desktop app. If **Remote** is missing on the phone, update the ChatGPT mobile app first. Feature availability may vary by rollout or workspace settings.

Official guide: [Remote connections](https://learn.chatgpt.com/docs/remote-connections)


## 2026-09-04 - Copy-friendly notebook cell pages created

The repository now contains a GitHub-rendered notebook cell library:

- [Cell library index](docs/notebook-cells/README.md)
- [Cell 1 - Configuration and safety guard](docs/notebook-cells/01-configuration-and-safety.md)
- [Cell 2 - Sample populated candidate props](docs/notebook-cells/02-sample-populated-props.md)
- [Cell 3 - Count populated candidate props](docs/notebook-cells/03-count-populated-props.md)

Each page contains a copyable Python block and navigation to the next cell. The root [README](README.md) also links to the library.

All three currently completed cells were synchronized from [the complete source file](notebooks/ssp_props_read_only_cells.py). Future notebook cells will be added to this library when they are created.
