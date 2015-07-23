# -*- coding: utf-8 -*-


from ipp_macro_series_parser.comptes_nationaux import cn_parser_tee
from ipp_macro_series_parser.comptes_nationaux import cn_main


def test_duplicate_tee_df():
    folder_year = 2013
    tee_df_by_year = cn_parser_tee.tee_df_by_year_generator(folder_year)
    for key, df in tee_df_by_year.items():
        for element in df.duplicated():
            assert element == 0, "There are duplicate rows in TEE " + key + ", in folder: comptes_annees " + folder_year


def test_cn_main1():
    try:
        cn_main.cn_df_generator(2013)
        result = True
    except:
        result = False
    assert result, "The final table of comptabilite nationale could not be generated in cn_main"
