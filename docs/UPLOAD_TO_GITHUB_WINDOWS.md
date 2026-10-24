# Publish WaveAssure to GitHub (Windows)

## Important

The WaveAssure v0.9.0 release is **research-only**. Never publish patient waveforms, hospital records, private keys, credentials, or clinical trial participant information. This repository contains no trained clinical model and provides no authorization for patient care.

### One-time setup

1. Extract the GitHub-ready ZIP to an independent folder on the D: drive, e.g. `D:\WaveAssure-GitHub`.
2. Install tools if missing:

   ```powershell
   winget install --id Git.Git -e
   winget install --id GitHub.cli -e
   ```

3. Restart PowerShell and authenticate **as ruthwikg-create** using your own browser:

   ```powershell
   gh auth login
   gh auth status
   ```

4. Set your local Git author name and verified email if Git requests them:

   ```powershell
   git config --global user.name "Your GitHub display name"
   git config --global user.email "Your verified GitHub email or GitHub no-reply address"
   ```

### Preview the safety checks

From the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-to-github.ps1 -CheckOnly
```

### Publish securely

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-to-github.ps1
```

The script only targets **`ruthwikg-create/WaveAssure`** and refuses a public repository. If the repository doesn't exist, GitHub CLI will create it as **private**. If it exists and is private, it pushes to the `main` branch without force-pushing. It also rejects local private patient/data/model artifacts before committing.

If the existing GitHub repository has unrelated history (e.g. an initialized README), a normal push may fail. Do **not** force-push; reconcile histories manually.

### After publishing

Visit: https://github.com/ruthwikg-create/WaveAssure

Keep the repository private until a maintainer performs a source, dependency, license, security, and privacy review. Public release is distinct from clinical use. **No clinical trial, ISO certification, or CDSCO approval is implied by publishing the code.**
