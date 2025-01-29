from Submodules.utils import store_balmorel_input, join_to_gpd
from pybalmorel import IncFile

def onshore_vre_func(ctx):
    
    # 1.3 Load and Save WND_VAR_T
    df = store_balmorel_input('WND_VAR_T', ['A', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'S', 'T', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='WND_VAR_T', path='Output',
                prefix='\n'.join([
                    "TABLE WND_VAR_T1(SSS,TTT,AAA) 'Variation of the wind generation'",
                    ""
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    ";",
                    "WND_VAR_T(AAA,SSS,TTT) = WND_VAR_T1(SSS,TTT,AAA);",
                    "WND_VAR_T1(SSS,TTT,AAA) = 0;",
                    "WND_VAR_T('Frederiksberg_A',SSS,TTT) = WND_VAR_T('Koebenhavn_A',SSS,TTT);",
                    "$onmulti",
                    "$if     EXIST '../data/OFFSHORE_WND_VAR_T.inc'      $INCLUDE '../data/OFFSHORE_WND_VAR_T.inc';",
                    "$if not EXIST '../data/OFFSHORE_WND_VAR_T.inc'      $INCLUDE '../../base/data/OFFSHORE_WND_VAR_T.inc';",
                    "$offmulti"
                ]))
    incfile.body_prepare(['S', 'T'],
                        ['A'])
    incfile.save()
    
    
    # 1.4 Load and Save SOLE_VAR_T
    df = store_balmorel_input('SOLE_VAR_T', ['A', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'S', 'T', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='SOLE_VAR_T', path='Output',
                prefix='\n'.join([
                    "TABLE SOLE_VAR_T1(SSS,TTT,AAA) 'Variation of the solar generation'",
                    ""
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    ";",
                    "SOLE_VAR_T(AAA,SSS,TTT) = SOLE_VAR_T1(SSS,TTT,AAA);",
                    "SOLE_VAR_T1(SSS,TTT,AAA) = 0;",
                    "SOLE_VAR_T('Frederiksberg_A',SSS,TTT) = SOLE_VAR_T('Koebenhavn_A',SSS,TTT);"
                ]))
    incfile.body_prepare(['S', 'T'],
                        ['A'])
    incfile.save()
    
    # 1.5 Load and save WNDFLH
    df = store_balmorel_input('WNDFLH', ['A', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='WNDFLH', path='Output',
                prefix='\n'.join([
                    "PARAMETER WNDFLH(AAA)  'Full load hours for solar power'",
                    "/"  
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    "/",
                    ";",
                    "$onmulti",
                    "$if     EXIST '../data/OFFSHORE_WNDFLH.inc' $INCLUDE '../data/OFFSHORE_WNDFLH.inc';",
                    "$if not EXIST '../data/OFFSHORE_WNDFLH.inc' $INCLUDE '../../base/data/OFFSHORE_WNDFLH.inc';",
                    "$offmulti"
                ]))
    incfile.body = incfile.body.pivot_table(index='A', values='Value', aggfunc='sum')
    
    # Hard-coded assumption on Frederiksberg 
    incfile.body.loc['Frederiksberg_A', 'Value'] = incfile.body.loc['Koebenhavn_A', 'Value']
    
    incfile.body.index.name = ''
    incfile.body.columns = ['']
    incfile.save()
    
    # 1.6 Load and save SOLEFLH
    df = store_balmorel_input('SOLEFLH', ['A', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'Value', 'A'], '_A')

    
    incfile = IncFile(name='SOLEFLH', path='Output',
                prefix='\n'.join([
                    "PARAMETER SOLEFLH(AAA)  'Full load hours for solar power'",
                    "/"  
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    "/",
                    ";"
                ]))
    incfile.body = incfile.body.pivot_table(index='A', values='Value', aggfunc='sum')
    
    # Hard-coded assumption on Frederiksberg 
    incfile.body.loc['Frederiksberg_A', 'Value'] = incfile.body.loc['Koebenhavn_A', 'Value']
    
    incfile.body.index.name = ''
    incfile.body.columns = ['']
    incfile.save()
    
    # 1.8 Get VRE Potentials
    df = store_balmorel_input('SUBTECHGROUPKPOT', ['CRA', 'TECH_GROUP', 'SUBTECH_GROUP', 'Value'],
                            ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                            lambda x: x.loc[x.CRA.str.contains('DK_')])
        
    ## Join municipal codes ('CRA') to names ('NAME_2')
    df = join_to_gpd(df, 'CRA', ctx.obj['mun'], 'NAME_2', 
                      ['CRA', 'TECH_GROUP', 'SUBTECH_GROUP', 'Value', 'A'], '_A')
    df['A'] = df.A + '_A'
    
    
    # Convert very small numbers to EPS
    idx = df.Value < 1e-10
    df.loc[idx, 'Value'] = 'EPS'
    
    incfile = IncFile(name='SUBTECHGROUPKPOT', path='Output',
                prefix='\n'.join([
                    "TABLE SUBTECHGROUPKPOT(CCCRRRAAA, TECH_GROUP, SUBTECH_GROUP)  'Subtechnology group capacity restriction by geography (MW)'",
                    ""  
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    ";",
                    "$onmulti",
                    "$if     EXIST '../data/SUBTECHGROUPKPOT2.inc' $INCLUDE '../data/SUBTECHGROUPKPOT2.inc';",
                    "$if not EXIST '../data/SUBTECHGROUPKPOT2.inc' $INCLUDE '../../base/data/SUBTECHGROUPKPOT2.inc';",
                    "$offmulti",
                    "$onmulti",
                    "$if     EXIST '../data/OFFSHORE_SUBTECHGROUPKPOT.inc' $INCLUDE '../data/OFFSHORE_SUBTECHGROUPKPOT.inc';",
                    "$if not EXIST '../data/OFFSHORE_SUBTECHGROUPKPOT.inc' $INCLUDE '../../base/data/OFFSHORE_SUBTECHGROUPKPOT.inc';",
                    "$offmulti"
                ]))
    incfile.body_prepare(['A', 'TECH_GROUP'], 'SUBTECH_GROUP', values='Value')
    # incfile.body.index.names = ['', '']
    # incfile.body.columns.name = ''
    incfile.save()
    