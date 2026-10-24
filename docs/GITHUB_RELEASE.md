# Publishing the research-only WaveAssure project to GitHub

No connected WaveAssure repository was found during the v0.9 audit, so **no GitHub changes have been made**. Do not overwrite unrelated biomedical repositories. If you want a connected GitHub workflow, first create a **private, empty** repository named `WaveAssure` through https://github.com/new and share its repository URL in ChatGPT. The assistant can then work with the GitHub connector against that repository.

Alternative local upload, after reviewing code and protecting all research files:

```powershell
cd D:\WaveAssure-v0.9\WaveAssure
git init
git branch -M main
git add .
git status --short
git commit -m "WaveAssure research-only 0.9 safety controls"
git remote add origin https://github.com/YOUR_USERNAME/WaveAssure.git
git push -u origin main
```

This is a sample command sequence **not executed in your GitHub account**. Ensure Git is installed and replace the placeholder URL. Do not commit patient data, real `.dat` files, model signing private keys, reviewer passwords, database files, or secrets. Verify the Git staging output. This release is research-only and must not be advertised as clinically validated.
