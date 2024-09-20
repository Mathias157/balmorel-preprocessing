
import pickle

conversion_dictionaries = {
    

    'coord_names' : {'municipality' : 'R',
                                'user' : 'DEUSER',
                                'year' : 'Y',
                            'week' : 'S',
                            'hour' : 'T'},

    'coord_element_names' : {'user' : {'industry' : 'PII',
                            'public' : 'OTHER',
                            'residential' : 'RESE'}},

    'week_to_seasons' : ['S0%d'%i for i in range(1, 10)] +\
                        ['S%d'%i for i in range(10, 53)],
                        
    'hour_to_terms'  : ['T00%d'%i for i in range(1, 10)] +\
                       ['T0%d'%i for i in range(10, 100)] +\
                       ['T%d'%i for i in range(100, 169)]

}

with open('Modules/Submodules/conversion_dictionaries.pkl', 'wb') as f:
    pickle.dump(conversion_dictionaries, f)