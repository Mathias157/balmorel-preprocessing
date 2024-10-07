from Submodules.utils import store_balmorel_input, join_to_gpd
from pybalmorel import IncFile

def heat_profiles_func(ctx):
    
    # Load DH_VAR_T
    df = store_balmorel_input('DH_VAR_T', ['A', 'DHUSER', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')].query("DHUSER == 'RESH'"))
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'DHUSER', 'S', 'T', 'Value', 'A'], '_A')
        
    ### Save DH_VAR_T.inc
    incfile = IncFile(name='DH_VAR_T', path='Output',
                    prefix='\n'.join([
                            "PARAMETER DH_VAR_T(AAA,DHUSER,SSS,TTT) 'Variation in heat demand';",
                            "TABLE DH_VAR_T1(SSS,TTT,AAA,DHUSER)",
                            ""
                    ]),
                    body=df,
                    suffix='\n'.join([
                            "",
                            ";",
                            "DH_VAR_T(AAA,'RESH',SSS,TTT) = DH_VAR_T1(SSS,TTT,AAA,'RESH');",
                            "DH_VAR_T1(SSS,TTT,AAA,DHUSER) = 0;",
                            "DH_VAR_T('Herlev_A','RESH',SSS,TTT) = DH_VAR_T('Ballerup_A','RESH',SSS,TTT);"
                    ]))
    incfile.body_prepare(['S', 'T'],
                        ['A', 'DHUSER'])
    incfile.save()
    
    ### Save INDIVUSERS_DH_VAR_T
    df['A'] = df.A.str.replace('_A', '_IDVU-SPACEHEAT')
    df['DHUSER'] = 'RESIDENTIAL'
    incfile = IncFile(name='INDIVUSERS_DH_VAR_T', path='Output',
                    prefix='\n'.join([
                    "TABLE DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER)",
                    ""
                    ]),
                    body=df,
                    suffix='\n'.join([
                        "",
                        ";",
                        "DH_VAR_T(AAA,DHUSER,SSS,TTT)$(SUM((S,T), DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER))) = DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER);",
                        "DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER) = 0;",
                        "DH_VAR_T('Herlev_A','RESIDENTIAL',SSS,TTT) = DH_VAR_T('Ballerup_A','RESIDENTIAL',SSS,TTT);"
                    ]))
    incfile.body_prepare(['S', 'T'],
                        ['A', 'DHUSER'])
    incfile.save()