
import pickle

conversion_dictionaries = {
    

    'coord_names' : {'municipality' : 'R',
                                'user' : 'DEUSER',
                                'year' : 'Y',
                            'week' : 'S',
                            'hour' : 'T'},

    'coord_element_names' : {'user' : {'industry' : 'PII',
                            'public' : 'OTHER',
                            'residential' : 'RESE'}} |\
                        {'week' : {str(i) : 'S0%d'%i for i in range(1, 10)} |\
                                    {str(i) : 'S%d'%i for i in range(10, 53)}} |\
                        {'hour' : {str(i) : 'T00%d'%i for i in range(1, 10)} |\
                                    {str(i) : 'T0%d'%i for i in range(10, 100)} |\
                                    {str(i) : 'T%d'%i for i in range(100, 169)}}

}

with open('Modules/Submodules/conversion_dictionaries.pkl', 'wb') as f:
    pickle.dump(conversion_dictionaries, f)