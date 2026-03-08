# Scenario 2: LDR Validation Data

Place .ldr files here for structural validation training.

Optionally include a `labels.csv` with columns:
```
filename,label
building1.ldr,0
building2.ldr,1
```

Where 0=pass, 1=fail.

Run `scripts/scenario2/feature_engineering.py` to extract features into `features.csv`.
