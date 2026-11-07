# JDownloader 2 Progress Bar Color Changer

Change the **download-list progress bar fill** to any RGB HEX color, independently of table text, without installing a theme.

**No JDownloader binaries are distributed.** The tool patches the user's locally installed `JDownloader.jar`.

## Quick start (Windows)

1. Install **Python 3.8+** (ensure `py` works in PowerShell).
2. Download this repository (Code → Download ZIP) and extract it.
3. **Close JDownloader completely**, including the system tray icon.
4. Open **PowerShell as Administrator** in the extracted folder (Administrator required if JDownloader is under Program Files).
5. Run:

   ```powershell
   py -3 .\scripts\change_progress_color.py --color "#64B5F6"
   ```

6. Restart JDownloader.

Choose another color by running the same command with a different HEX code after closing JDownloader.

### Custom installation directory

```powershell
py -3 .\scripts\change_progress_color.py --color "#00D4FF" --jd-dir "D:\Apps\JDownloader"
```

### Examples

| Color | HEX |
| --- | --- |
| Light blue | `#64B5F6` |
| Cyan | `#00D4FF` |
| Deep sky blue | `#00BFFF` |
| Green | `#00E676` |
| Orange | `#FFB74D` |

## Compatibility and safety

- **Version-specific:** Supports the original renderer class from the tested November 2026 JDownloader build and its matching patched variant. Other JDownloader versions are **not yet supported**; the script refuses unknown class versions.
- A timestamped backup is made before replacing `JDownloader.jar`.
- The patched JAR is written to a temporary file and ZIP-tested before replacement.
- Updates may overwrite the modification; rerun only if the new version is supported.
- This is an **unofficial community project**, not affiliated with JDownloader.
- Test first on a backed-up installation; no guarantee is made for other environments.

## Restore

1. Close JDownloader.
2. Find the backup printed by the script, e.g. `JDownloader.jar.backup-...`.
3. Rename the current `JDownloader.jar` to something else and copy the backup back as `JDownloader.jar`.
4. Restart JDownloader.

## How it works

The tool checks the SHA-256 of the `RendererProgressBar.class` entry inside the installed JAR. For the supported stock class, it applies a minimal binary delta to add a `getForeground()` override that returns the chosen `java.awt.Color`. For a previously patched supported class, it updates the RGB operands. It does not distribute JDownloader class files or a modified JAR.

## Contributing

To support another JDownloader release, open an issue with the renderer class SHA-256, Java version, and JDownloader build information. **Do not upload proprietary JARs without permission.** Any additional binary patches must be reviewed and tested against their exact class version.

## License

MIT applies to the original scripts and documentation only. JDownloader retains its own licenses.
