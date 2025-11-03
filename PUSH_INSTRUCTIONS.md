# GitHub Push Instructions - Personal Access Token

## Step 1: Create a Personal Access Token (if you don't have one)

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `LNSAPP-Token`
4. Set expiration: Choose your preference (30 days, 60 days, or No expiration)
5. Select scopes:
   - ✅ **repo** (Full control of private repositories)
   - This gives you push access
6. Click **"Generate token"** at the bottom
7. **IMPORTANT**: Copy the token immediately (it won't be shown again!)
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 2: Push with the Token

Once you have your token, run this command in PowerShell:

```powershell
git push https://YOUR_TOKEN_HERE@github.com/JeriahC-ptsa/LNSAPP.git main
```

**Replace `YOUR_TOKEN_HERE` with your actual token.**

Example:
```powershell
git push https://ghp_abc123xyz789@github.com/JeriahC-ptsa/LNSAPP.git main
```

## Alternative: Store Token in Git Credential Manager

To avoid typing the token every time:

```powershell
git config --global credential.helper manager-core
git push origin main
```

When prompted:
- Username: Your GitHub username
- Password: Paste your Personal Access Token (NOT your GitHub password)

## What Will Be Pushed

✅ **Commit**: `Add password visibility toggle and confirmation feature`

**Files:**
- auth.py (password validation)
- templates/admin/users.html (password confirmation UI)
- templates/login.html (password visibility toggle)
- ADMIN_ACCESS_FIX.md (documentation)
- PASSWORD_VISIBILITY_FEATURE.md (documentation)
- add_admin_permissions.py (admin permissions script)

**Total**: 6 files changed, 556 insertions(+)

## Troubleshooting

### Error: "Authentication failed"
- Make sure you copied the entire token
- Token should start with `ghp_`
- Check that token has `repo` scope enabled

### Error: "Permission denied"
- Verify you have write access to JeriahC-ptsa/LNSAPP repository
- Check that token hasn't expired

### Error: "Repository not found"
- Verify the repository name is correct: `JeriahC-ptsa/LNSAPP`

## Security Note

⚠️ **Never share your Personal Access Token!**
- Treat it like a password
- Don't commit it to your repository
- Don't share it in screenshots or messages
- If compromised, revoke it immediately at: https://github.com/settings/tokens

---

**Ready to push?** Get your token from GitHub and run the push command!
