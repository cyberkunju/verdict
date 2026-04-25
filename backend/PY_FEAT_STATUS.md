# py-feat probe status

Date: 2026-04-25

## What was tried

Inside `backend/.venv`:

```bash
.venv/bin/pip install --no-deps py-feat
.venv/bin/python -c "import feat"
```

## Result

Install succeeded, import failed.

Observed failure:

```text
ModuleNotFoundError: No module named 'pandas'
```

## Conclusion

`py-feat --no-deps` does not import cleanly in the minimal backend venv. The
existing deterministic fallback AU path should remain the default in this repo
until the full transitive dependency stack is provisioned and verified.

## Next step if revisiting

Provision the documented dependency stack in an isolated environment, then retry:

```bash
pip install --no-deps py-feat
pip install pandas seaborn matplotlib torch torchvision pillow scikit-learn
python -c "import feat"
```
