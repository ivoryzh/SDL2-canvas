import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def rolling_mean(df, x_col, y_col, window_size=20, min_periods=None):
    if min_periods is None:
        min_periods = window_size

    df_sorted = df.sort_values(by=x_col).copy()

    result = (
        df_sorted[y_col].rolling(window=window_size, min_periods=min_periods).mean()
    )

    if not df.equals(df_sorted):
        return result.reindex(df.index)
    return result


def detect_peaks(
    df,
    x_col,
    y_col,
    height=None,
    prominence=1,
    distance=None,
    width=None,
    threshold=None,
    noise_tolerance=1e-6,
):
    df_sorted = df.sort_values(by=x_col).copy()

    x_values = df_sorted[x_col].values
    x_gradient = np.gradient(x_values)

    window_size = min(5, len(x_gradient) // 10 + 1)
    if window_size > 1:
        smoothed_gradient = np.convolve(
            x_gradient, np.ones(window_size) / window_size, mode="valid"
        )

        pad_size = len(x_gradient) - len(smoothed_gradient)
        pad_left = pad_size // 2
        pad_right = pad_size - pad_left
        smoothed_gradient = np.pad(smoothed_gradient, (pad_left, pad_right), "edge")
    else:
        smoothed_gradient = x_gradient

    forward_mask = smoothed_gradient >= noise_tolerance
    reverse_mask = smoothed_gradient < -noise_tolerance

    if not np.any(forward_mask) or not np.any(reverse_mask):
        peak_indices, _ = find_peaks(
            df_sorted[y_col].values,
            height=height,
            prominence=prominence,
            distance=distance,
            width=width,
            threshold=threshold,
        )
        peaks_df = (
            df_sorted.iloc[peak_indices].copy()
            if len(peak_indices) > 0
            else pd.DataFrame()
        )
        if not peaks_df.empty:
            peaks_df["scan_direction"] = "unknown"
        return peaks_df

    df_forward = df_sorted[forward_mask].copy()
    df_reverse = df_sorted[reverse_mask].copy()

    def find_scan_peaks(scan_df, direction):
        if scan_df.empty:
            return pd.DataFrame()

        y_values = scan_df[y_col].values
        peak_indices, properties = find_peaks(
            y_values,
            height=height,
            prominence=prominence,
            distance=distance,
            width=width,
            threshold=threshold,
        )

        if len(peak_indices) == 0:
            return pd.DataFrame()

        peaks_df = scan_df.iloc[peak_indices].copy()

        peaks_df["scan_direction"] = direction

        if height is not None and "peak_heights" in properties:
            peaks_df["peak_height"] = properties["peak_heights"]
        if "prominences" in properties:
            peaks_df["prominence"] = properties["prominences"]
        if "widths" in properties:
            peaks_df["width"] = properties["widths"]

        return peaks_df

    forward_peaks = find_scan_peaks(df_forward, "forward")
    reverse_peaks = find_scan_peaks(df_reverse, "reverse")

    all_peaks = pd.concat([forward_peaks, reverse_peaks])

    if all_peaks.empty:
        return pd.DataFrame()

    all_peaks = all_peaks.sort_values(by=x_col)
    all_peaks = all_peaks.reset_index(drop=True)

    if not df.equals(df_sorted):
        result = all_peaks.copy()
        return result

    return all_peaks
