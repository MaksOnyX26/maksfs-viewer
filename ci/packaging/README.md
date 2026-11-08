# Windows packaging continuation

The successful compile run #2 is https://github.com/MaksOnyX26/maksfs-viewer/actions/runs/42509539984
(source `9daa67a268f11abbb3f62ee1dafdd5f6ee223ef5`). Its only saved artifact is
`maksfs-windows-diagnostics-42509539984-1` (77,037 bytes). The workflow explicitly
excluded binaries and had no build cache. Its hosted runner has completed.
One recovery compile is therefore technically necessary; this is not a project restart.

The new packaging workflow preserves `maksfs-packaging-inputs-<run id>` **before**
packaging. Subsequent packaging runs automatically reuse the newest non-expired
snapshot from this branch. A dispatch can select `source_run_id` explicitly.
The old successful build workflow and compiler settings remain unchanged.

`stage.py` uses the upstream full packaging manifest, including shaders, skins,
fonts, CEF/VLC, WebRTC and the MSVC app-local runtime. Copy-only build output is
not a complete distribution. The final installer step is replaced by a per-user
NSIS installer with an explicit file list; uninstall preserves unknown/user files.
The portable launcher sets process-local APPDATA/LOCALAPPDATA beneath `data`.

Continuation after interruption: inspect the newest **MaksFS Windows packages**
run on `maksfs-main`. If building, wait; do not start another compile. If packaging
failed, fix packaging scripts and push them: the preserved snapshot is reused.
Never rerun the old compile-only workflow to obtain distributable binaries.
Download the packages artifact only after validation succeeds. Inspect
`verification.json`, `SHA256SUMS.txt`, and `installer-test.txt`. Windows 11 desktop,
GPU, Second Life login, voice and media still require interactive testing.
