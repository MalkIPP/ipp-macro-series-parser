# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 18:00:33 2015

@author: sophie.cottet
"""

import logging
import pandas
from py_expression_eval import Parser


log = logging.getLogger(__name__)


def look_up(df, entry_by_index, years = range(1949, 2014)):
    """
    Get the data corresponding to the parameters (code, institution, ressources, year, description) defined in the
    dictionnary "entry_by_index", from the DataFrame df containing the stacked Comptabilité Nationale data.
    Note that entering any entry_by_index containing a 'formula' key will give an empty Series.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    entry_by_index : dictionnary
        A dictionnary with keys 'code', 'institution', 'ressources', 'year', 'description'.

    Example
    --------
    >>> from ipp_macro_series_parser.comptes_nationaux.cn_parser_main import get_comptes_nationaux_data
    >>> table2013 = get_comptes_nationaux_data(2013)
    >>> dico = {'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False, 'year': None, 'description': 'PIB'}
    >>> df0 = look_up(table2013, dico)

    Returns a slice of get_comptes_nationaux_data(2013) containing only the gross product (PIB) of the whole economy
    (S1), for all years.
    """
    result = df.copy()
    result = result[df['year'].isin(years)].copy()
    for key, value in entry_by_index.items():
        if value is None:
            continue
        if key == 'drop':
            continue
        if key != 'description' and key != 'formula':
            try:
                result = result[df[key] == value].copy()
            except KeyError:
                log.info('{} {} is not available'.format(key, value))
                raise
            if result.empty:
                log.info('Variable {} is not available'.format(value))
                result = pandas.DataFrame()
        elif key == 'description':
            result = result[df[key].str.contains(value)].copy()
        else:
            result = pandas.DataFrame()
    return result


def look_many(df, entry_by_index_list):
    """
    Get the multiple data corresponding to the parameters (the tuples (code, institution, ressources, year,
    description)) defined in the list of dictionnaries "entry_by_index_list", from the DataFrame df containing the
    stacked Comptabilité Nationale data.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    entry_by_index_list : list of dictionnaries
        Dictionnaries should have keys 'code', 'institution', 'ressources', 'year', 'description', but not necesarily
        all of them.

    Example
    --------
    >>> table2013 = get_comptes_nationaux_data(2013)
    >>> my_list = [{'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False},
        ...         {'code': 'B1n/PIN', 'institution': 'S1', 'ressources': False}]
    >>> df1 = look_many(table2013, my_list)

    Returns a slice of get_comptes_nationaux_data(2013) containing the gross product (PIB) and the net product (PIN) of
    the whole economy (S1), for all years.

    >>> my_list_2 = [{'code': None, 'institution': 'S1', 'ressources': False,
    ...             'description': 'PIB'},
    ...             {'code': None, 'institution': 'S1', 'ressources': False,
    ...             'description': 'PIN'}]
    >>> df2 = look_many(table2013, my_list_2)

    Returns the same output, using a keyword from the description.
    """
    df_output = pandas.DataFrame()
    for entity in entry_by_index_list:
        df_inter = look_up(df, entity)
        df_output = pandas.concat([df_output, df_inter], axis = 0, ignore_index=False, verify_integrity=False)
    df_output = df_output.drop_duplicates()
    return df_output


def get_or_construct_value(df, variable_name, index_by_variable, years = range(1949, 2014)):
    """
    Returns the DateFrame (1 column) of the value of economic variable(s) for years of interest.
    Years are set to the index of the DataFrame.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    variable : string or dictionary
        Variable to get or to construct (by applying formula).
    index_by_variable : dictionary
        Contains all economic variables indexes and formula. Variables appearing in formula of variable should be
        listed in index_by_variable.
    years : list of integers
        Years of interest

    Example
    --------
    >>> table_cn = get_comptes_nationaux_data(2013)
    >>> index_by_variable = {
    ...    'Interets_verses_par_rdm': {
    ...         'code': 'D41',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Dividendes_verses_par_rdm_D42': {
    ...         'code': 'D42',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Dividendes_verses_par_rdm_D43': {
    ...         'code': 'D43',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Revenus_propriete_verses_par_rdm': {
    ...         'code': 'D44',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Interets_dividendes_verses_par_rdm': {
    ...         'code': None,
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': 'Interets et dividendes verses par RDM, nets',
    ...         'formula': 'Interets_verses_par_rdm + Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm'
    ...     }
    ... }
    >>> computed_variable_vector, computed_variable_formula = get_or_construct(
    ...     df, 'Interets_dividendes_nets_verses_par_rdm', index_by_variable
    ...     )

    Returns a tuple, where the first element is a DataFrame (with a single column) for years 1949 to 2013 of the value
    of the sum of the four variables, and the second element is the formula 'Interets_verses_par_rdm +
    Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm'
    """
    assert df is not None
    df = df.copy()
    assert variable_name is not None
    if index_by_variable is None:
        index_by_variable = {
            variable_name: {'code': variable_name}
            }
    variable = index_by_variable[variable_name]
    formula = variable.get('formula')
    dico_value = dict()

    entry_df = look_up(df, variable, years)

    if not entry_df.empty:
        entry_df = entry_df.set_index('year')
        serie = entry_df[['value']].copy()
        assert len(serie.columns) == 1
        serie.columns = [variable_name]
        final_formula = variable_name

    # For formulas that are not real formulas but taht are actually a mapping
    elif not formula and entry_df.empty:
        serie = pandas.DataFrame()
        final_formula = ''

    else:
        print variable_name
        parser_formula = Parser()
        expr = parser_formula.parse(formula)
        variables = expr.variables()

        for component in variables:
            print component
            print 'years', years
            variable_value, variable_formula = get_or_construct_value(df, component, index_by_variable, years)
            print 'for', component, ': length of variable_value', len(variable_value)
            formula_with_parenthesis = '(' + variable_formula + ')'  # needs to be edited for a nicer style of formula output
            final_formula = formula.replace(component, formula_with_parenthesis)
            dico_value[component] = variable_value.values.squeeze()
            index = variable_value.index

        formula_modified = formula.replace("^", "**")

        print formula
        for component in variables:
            print len(dico_value[component])
        data = eval(formula_modified, dico_value)
        assert data is not None
        print variable_name
        print data
        print index
        serie = pandas.DataFrame(
            data = {variable_name: data},
            index = index,
            )

#    serie.columns = serie.columns.str.replace('_', ' ')
#    final_formula = final_formula.replace('_', ' ')

    return serie, final_formula


def get_or_construct_data(df, variable_dictionary, years = range(1949, 2014)):
    """
    Returns the DateFrame of the values of economic variables, fetched or calculated, for years of interest.
    Years are set to the index of the DataFrame.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    variable_dictionary : dictionary
        Contains all economic variables denoted by their index. Variables for which formula is None will be directly
        fetched in the comptabilité nationale data (df). Those for which formula is not None will be calculated.
        Variables appearing in formulas should be in the index of variable_dictionary. If not interested in values of
        a variable, add 'drop':True in sub-dictionary variable_dictionary[variable].
    years : list of integers
        Years of interest

    Example
    --------
    >>> table_cn = get_comptes_nationaux_data(2013)
    >>> dict_RDM = {
    ...    'Interets_verses_par_rdm': {
    ...         'code': 'D41',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...     },
    ...    'Dividendes_verses_par_rdm_D42': {
    ...         'code': 'D42',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Dividendes_verses_par_rdm_D43': {
    ...         'code': 'D43',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Revenus_propriete_verses_par_rdm': {
    ...         'code': 'D44',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Interets_verses_au_rdm': {
    ...         'code': 'D41',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Dividendes_verses_au_rdm_D42': {
    ...         'code': 'D42',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Dividendes_verses_au_rdm_D43': {
    ...         'code': 'D43',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Revenus_propriete_verses_au_rdm': {
    ...         'code': 'D44',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Interets_dividendes_verses_par_rdm': {
    ...         'code': None,
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': 'Interets et dividendes verses par RDM',
    ...         'formula': 'Interets_verses_par_rdm + Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm'
    ...    },
    ...    'Interets_dividendes_nets_verses_par_rdm': {
    ...         'code': None,
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': 'Interets et dividendes verses par RDM, nets',
    ...         'formula': 'Interets_verses_par_rdm + Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm - Interets_verses_au_rdm - Dividendes_verses_au_rdm_D42 - Dividendes_verses_au_rdm_D43 - Revenus_propriete_verses_au_rdm'
    ...    }
    ... }
    >>> values_RDM, formulas_RDM = get_or_construct_data(df, dict_RDM)

    Returns a tuple, where the first element is a DataFrame for years 1949 to 2013 containing the sum of interests and
    dividends paid to France by the rest of the world, both gross and net of interests and dividends paid by France to
    the rest of the world ; and the second element is the dictionary of formulas, indexed by the calculated variables.
    """
    print 'years', years
    result = pandas.DataFrame()
    formulas = dict()

    for variable in variable_dictionary:
        print variable
        print 'years', years
        variable_values, variable_formula = get_or_construct_value(df, variable, variable_dictionary, years)
        variable_name = variable.replace('_', ' ')

        if variable_dictionary[variable].get('formula') is not None:
            formulas[variable_name] = variable_formula

        drop = variable_dictionary[variable].get('drop')
        if not drop:
            result = pandas.concat((result, variable_values), axis=1)
        else:
            continue

    return result, formulas
