# GitHub and Streamlit deployment

## Route 1 — GitHub website upload

1. Extract the downloadable project ZIP onto your computer. The extracted `FuelCell-Mat` folder is the repository root.
2. Log in to GitHub and create a **public repository** named `FuelCell-Mat`. Do not tick options to create an extra README or .gitignore.
3. On the new repository, select **Add file → Upload files**. Upload **the contents of** `FuelCell-Mat`, including the `fuelcell_mat`, `docs`, `tests`, `examples` and `.streamlit` directories. Do not upload the ZIP as the only file. Ensure `app.py` and `requirements.txt` are at the repository root.
4. Commit the upload. If the browser omits hidden folders, use Route 2 or create `.streamlit/config.toml` manually; it is optional for functionality.
5. Open [Streamlit Community Cloud](https://share.streamlit.io), connect your GitHub account, and select your repository, default branch and **main file `app.py`**. Deploy.
6. Confirm that **Calculator** and the **Calculate fuel-cell performance** button appear on the main page. Press Calculate using the defaults; verify the four summary results, the **Performance curves**, **Materials comparison**, **Sensitivity study**, **Equations & limitations** and **Export results** tabs, and the CSV download.

## Route 2 — Command line

From inside the extracted project folder:

```bash
git init
git branch -M main
git add .
git commit -m "Initial FuelCell-Mat release"
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/FuelCell-Mat.git
git push -u origin main
```

Create the empty repository on GitHub before pushing. Change `YOUR-GITHUB-USERNAME` to your actual account username.

## Run on your computer

```bash
python -m venv .venv
```

Activate the environment with `.venv\Scripts\Activate.ps1` on Windows PowerShell or `source .venv/bin/activate` on macOS/Linux. Then:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The application runs without credentials, external accounts, databases or APIs. Use Python 3.11 or later; Python 3.12 is the recommended deployment choice.

## Common deployment issues

- **Module not found:** confirm `fuelcell_mat/__init__.py` and all package files are uploaded, alongside root-level `app.py`.
- **Requirements not installed:** keep `requirements.txt` in the repository root.
- **App not found:** select the main file path `app.py`, not `fuelcell_mat/model.py`.
- **Hidden theme folder missing:** `.streamlit/config.toml` affects styling only; it is not required for core functionality.
- **Extreme settings return blank power:** this is an intentional guard for nonpositive modeled voltage. Reduce membrane resistance or current density.
- **Charts display no points:** select valid inputs, verify the current density remains below the limiting-current parameter, and press **Calculate fuel-cell performance** again.
- **No results after launch:** this is expected until you press **Calculate fuel-cell performance**. The form is in the main page, with additional inputs under **Advanced settings**.

## Maintenance

For mathematical changes, update the equations in `docs/MODEL.md` and run `pytest` before redeploying. The Streamlit application redeploys after committing changes to the connected branch.
