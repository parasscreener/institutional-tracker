import pandas as pd
import numpy as np


def assign_confidence(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df['confidence'] = []
        return df

    quantity_known = df['current_position'].notna() & df['transaction_volume'].notna()
    strong_entry = df['action_type'].isin(['Entry', 'Accumulation']) & quantity_known & (df['change_pct'] > 0)
    strong_exit = df['action_type'].isin(['Exit', 'Reduction']) & quantity_known & (df['change_pct'] <= -25)
    weight_only = (~quantity_known) & df['action_type'].isin(['Entry', 'Accumulation', 'Exit', 'Reduction'])

    df['confidence'] = np.select(
        [strong_entry | strong_exit, weight_only],
        ['High', 'Medium'],
        default='Low'
    )
    return df
