from typing import Union

import pandas as pd


def convert_to_jst(
    df_or_index: Union[pd.DataFrame, pd.Index], from_unit: str = "ms"
) -> Union[pd.DataFrame, pd.Index]:
    """
    Unix timestamp（ミリ秒）のインデックスを日本時間に変換する

    Parameters:
    -----------
    df_or_index : Union[pd.DataFrame, pd.Index]
        変換対象のDataFrameまたはIndex
    from_unit : str, default="ms"
        入力のタイムスタンプの単位 ("ms" または "s")

    Returns:
    --------
    Union[pd.DataFrame, pd.Index]
        日本時間に変換されたDataFrameまたはIndex

    Examples:
    --------
    DataFrameの場合:
    >>> df = pd.DataFrame({'close': [100, 200]}, index=[1709692800000, 1709692860000])
    >>> convert_to_jst(df)
                                 close
    2024-03-06 12:00:00+09:00    100
    2024-03-06 12:01:00+09:00    200

    Indexの場合:
    >>> idx = pd.Index([1709692800000, 1709692860000])
    >>> convert_to_jst(idx)
    DatetimeIndex(['2024-03-06 12:00:00+09:00', '2024-03-06 12:01:00+09:00'],
                  dtype='datetime64[ns, Asia/Tokyo]')

    秒単位の場合:
    >>> df = pd.DataFrame({'close': [100]}, index=[1709692800])
    >>> convert_to_jst(df, from_unit='s')
                                 close
    2024-03-06 12:00:00+09:00    100
    """
    if isinstance(df_or_index, pd.DataFrame):
        df_or_index.index = (
            pd.to_datetime(df_or_index.index, unit=from_unit)
            .tz_localize("UTC")
            .tz_convert("Asia/Tokyo")
        )
    else:
        df_or_index = (
            pd.to_datetime(df_or_index, unit=from_unit)
            .tz_localize("UTC")
            .tz_convert("Asia/Tokyo")
        )

    return df_or_index
