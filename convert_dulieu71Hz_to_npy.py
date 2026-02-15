# convert_dulieu71Hz_to_npy.py
import os
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm
from numpy.lib.format import read_magic, read_array_header_1_0, read_array_header_2_0

# Root directory of the dataset
ROOT_DIR = "./Dulieu/dulieu71Hz"

def _npy_shape(path: str):
    # Fast header-only read to avoid mmap handles (important on Windows when overwriting files).
    with open(path, "rb") as f:
        major, minor = read_magic(f)
        if (major, minor) == (1, 0):
            shape, _, _ = read_array_header_1_0(f)
        elif (major, minor) == (2, 0):
            shape, _, _ = read_array_header_2_0(f)
        else:
            # Fallback for newer versions
            arr = np.load(path, allow_pickle=False)
            return getattr(arr, "shape", None)
        return shape

def _select_dx_data(df: pd.DataFrame) -> np.ndarray:
    # Prefer selecting by column names containing "DX" (e.g. "c DX", "b DX", "a DX")
    dx_cols = [c for c in df.columns if isinstance(c, str) and ("DX" in c.upper())]
    if dx_cols:
        return df.loc[:, dx_cols].to_numpy(dtype=np.float32)

    # Fallback: assume layout like [Time, c_DX, c_DY, b_DX, b_DY, a_DX, a_DY]
    # -> take odd indices 1,3,5
    if df.shape[1] >= 6:
        idx = [1, 3, 5]
        return df.iloc[:, idx].to_numpy(dtype=np.float32)

    raise ValueError(f"Cannot infer DX columns from columns={df.columns.tolist()}")

def convert_xlsx_to_npy(root):
    # Find all .xlsx files recursively
    xlsx_files = glob.glob(os.path.join(root, "**", "*.xlsx"), recursive=True)
    # Exclude temporary files (starting with ~$)
    xlsx_files = [f for f in xlsx_files if not os.path.basename(f).startswith("~$")]
    
    print(f"Found {len(xlsx_files)} .xlsx files in {root}. Converting to .npy ...")
    
    count = 0
    err_count = 0 
    
    for xlsx_path in tqdm(xlsx_files):
        npy_path = xlsx_path.replace(".xlsx", ".npy")
        
        try:
            # Read Excel file
            # Example columns: ['Thời gian (s)', 'c DX', 'c DY', 'b DX', 'b DY', 'a DX', 'a DY']
            # We only keep the DX columns: ['c DX', 'b DX', 'a DX'].
            # engine='openpyxl' is needed for .xlsx
            df = pd.read_excel(xlsx_path, engine='openpyxl')

            data = _select_dx_data(df)

            # If .npy exists but has wrong channel count (e.g. previously saved DX+DY), overwrite it.
            if os.path.exists(npy_path):
                try:
                    old_shape = _npy_shape(npy_path)
                    if isinstance(old_shape, tuple) and len(old_shape) == 2 and old_shape[1] == data.shape[1]:
                        continue
                except Exception:
                    pass
            
            # Save as .npy
            np.save(npy_path, data)
            count += 1
            
        except Exception as e:
            print(f"\nError converting {xlsx_path}: {e}")
            err_count += 1

    print(f"Done. Converted {count} files. Errors: {err_count}")

if __name__ == "__main__":
    if not os.path.exists(ROOT_DIR):
        print(f"Directory not found: {ROOT_DIR}")
    else:
        convert_xlsx_to_npy(ROOT_DIR)
