# Pending private GitHub publication

The authenticated user endpoint returned HTTP 401. The connector exposes existing repository operations and has no private repository creation action. No remote was created. Authenticate with the normal browser flow:

```powershell
gh auth login -h github.com --web
gh auth status
$owner = gh api user --jq .login
gh repo view "$owner/MedCura-AI" --json nameWithOwner,isPrivate,visibility,url
```

Stop on an existing repository. Confirm a true not-found response while authenticated. Run from the release checkout only:

```powershell
gh repo create MedCura-AI --private --source . --remote origin --description "Reproducible inventory intelligence research for Saudi private medical complexes"
$settings = gh repo view "$owner/MedCura-AI" --json nameWithOwner,isPrivate,visibility,url | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $settings.nameWithOwner -ne "$owner/MedCura-AI" -or $settings.isPrivate -ne $true -or $settings.visibility -ne 'PRIVATE') { throw 'Privacy or repository identity could not be verified.' }
git push -u origin main
git push origin refs/tags/v1.0.0-research-prototype
gh repo view "$owner/MedCura-AI" --json nameWithOwner,isPrivate,visibility,defaultBranchRef,url
git ls-remote origin refs/heads/main refs/tags/v1.0.0-research-prototype
gh api "repos/$owner/MedCura-AI/contents/README.md?ref=main" --jq .name
```

