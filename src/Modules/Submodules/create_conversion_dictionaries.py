"""Is used to convert the easy-to-read-for-non-balmorel-user sets and elements to Balmorel input
"""
import pickle


# 1. Exogenous Electricity Demand xarray
exo_elec_dem_conversion_dictionaries = {
    

    'coord_names' : {'municipality' : 'R',
                                'user' : 'DEUSER',
                                'year' : 'Y',
                            'week' : 'S',
                            'hour' : 'T'},

    'coord_element_names' : {'user' : {'industry' : 'PII',
                            'public' : 'OTHER',
                            'residential' : 'RESE'},
                             'municipality' : {'æ' : 'ae',
                                               'ø' : 'oe',
                                               'å' : 'aa',
                                               'Æ' : 'Ae',
                                               'Ø' : 'Oe',
                                               'Å' : 'Aa'
                                 }},

    'week_to_seasons' : ['S0%d'%i for i in range(1, 10)] +\
                        ['S%d'%i for i in range(10, 53)],
                        
    'hour_to_terms'  : ['T00%d'%i for i in range(1, 10)] +\
                       ['T0%d'%i for i in range(10, 100)] +\
                       ['T%d'%i for i in range(100, 169)]

}

with open('Modules/Submodules/exo_elec_dem_conversion_dictionaries.pkl', 'wb') as f:
    pickle.dump(exo_elec_dem_conversion_dictionaries, f)
    

# 2. Exogenous Heat Demand xarray
exo_heat_dem_conversion_dictionaries = {
    

    'coord_names' : {'municipality' : 'A',
                                'user' : 'DHUSER',
                                'year' : 'Y'},

    'coord_element_names' : {'user' : {'district_heating' : 'RESH',
                                       'individual' : 'RESIDENTIAL',
                            'industry_phl' : 'IND-PHL',
                            'industry_phm' : 'IND-PHM',
                            'industry_phh' : 'IND-PHH'},
                             'municipality' : {'æ' : 'ae',
                                               'ø' : 'oe',
                                               'å' : 'aa',
                                               'Æ' : 'Ae',
                                               'Ø' : 'Oe',
                                               'Å' : 'Aa'
                                 }},

    'week_to_seasons' : ['S0%d'%i for i in range(1, 10)] +\
                        ['S%d'%i for i in range(10, 53)],
                        
    'hour_to_terms'  : ['T00%d'%i for i in range(1, 10)] +\
                       ['T0%d'%i for i in range(10, 100)] +\
                       ['T%d'%i for i in range(100, 169)]

}

with open('Modules/Submodules/exo_heat_dem_conversion_dictionaries.pkl', 'wb') as f:
    pickle.dump(exo_heat_dem_conversion_dictionaries, f)
    
    
# 3. Exogenous Grid xarray
exo_grid_conversion_dictionaries = {
    

    'coord_names' : {'municipality_from' : 'IRRRE',
                     'municipality_to' : 'IRRRI'},

    'coord_element_names' : {'municipality_from' : {'æ' : 'ae',
                                               'ø' : 'oe',
                                               'å' : 'aa',
                                               'Æ' : 'Ae',
                                               'Ø' : 'Oe',
                                               'Å' : 'Aa'
                                 },
                             'municipality_to' : {'æ' : 'ae',
                                               'ø' : 'oe',
                                               'å' : 'aa',
                                               'Æ' : 'Ae',
                                               'Ø' : 'Oe',
                                               'Å' : 'Aa'
                                 }},

}

with open('Modules/Submodules/exo_grid_conversion_dictionaries.pkl', 'wb') as f:
    pickle.dump(exo_grid_conversion_dictionaries, f)
    