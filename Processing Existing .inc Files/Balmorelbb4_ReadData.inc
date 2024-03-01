* File BalmorelBB4.inc for handling the Balbase4 model in Balmorel.
* First version 2009(hr) based on DTU Master project by Jesper Felstedt &QHYDROGEN_ Morten Middelboe Pedersen under supervision by Hans Ravn.
* Present version 20150428(hr), 20150430(Weiming), 20151217(hr), 20160810(hr), 20170419 (Juan and hr).
* Thanks to Weiming Xiong, Andreas von Recklinghausen and others for good contributions.

* The model is still under development.
* It will be available from www.balmorel.com under open source conditions.


* Efforts have been made to make a good model.
* However, most probably the model is incomplete and subject to errors.
* It is distributed with the idea that it will be usefull anyway,
* and with the purpose of getting the essential feedback,
* which in turn will permit the development of improved versions
* to the benefit of other user.
* Hopefully it will be applied in that spirit.

* All GAMS code of the Balmorel model is distributed under ICS license,
* see the license file in the base/model folder.


*-------------------------------------------------------------------------------
*-------------------------------------------------------------------------------
* Declarations and inclusion of data files:
*-------------------------------------------------------------------------------
*-------------------------------------------------------------------------------


*-------------------------------------------------------------------------------
*---- User defined SETS and ACRONYMS needed for data entry: --------------------
*-------------------------------------------------------------------------------

* Declarations: ----------------------------------------------------------------

* SETS:
* Geography related:
SET CCCRRRAAA         All geographical entities (CCC + RRR + AAA);
SET CCC(CCCRRRAAA)    "All Countries";
SET C(CCC)            "Countries in the simulation";
SET RRR(CCCRRRAAA)    "All regions";
SET AAA(CCCRRRAAA)    "All areas";
SET CCCRRR(CCC,RRR)   "Regions in countries";
SET RRRAAA(RRR,AAA)   "Areas in regions";
* The following three internal geography related sets are assigned in bb4datainc.inc:
SET IR(RRR)           "Regions in the simulation";
SET IA(AAA)           "Areas in the simulation";
SET ICA(CCC,AAA)      "Assignment of areas to countries in the simulation";
* Time related:
SET YYY               "All years";
SET SSS               "All seasons";
SET TTT               "All time periods";
SET Y(YYY)            "Years in the simulation";
SET S(SSS)            "Seasons in the simulation";
SET T(TTT)            "Time periods within the season in the simulation";
SET TWORKDAY(TTT)     "Time segments, T, in workdays";
SET TWEEKEND(TTT)     "Time segments, T, in weekends";
* Technology and fuel related:
SET GGG               "All generation technologies";
SET GDATASET          "Generation technology data";
SET FFF               "Fuels";
SET FDATASET          "Characteristics of fuels";
SET HYRSDATASET       "Characteristics of hydro reservoirs";
SET G(GGG)            "Generation technologies in the simulation";
SET AGKN(AAA,GGG)     "Areas for possible location of new technologies";
* Demand related:
SET DEUSER            "Electricity demand user groups. Set must include element RESE for holding demand not included in any other user group";
SET DHUSER            "Heat demand user groups. Set must include element RESH for holding demand not included in any other user group";
SET DF_QP             "Quantity and price information for elastic demands";
SET DEF               "Steps in elastic electricity demand";
SET DEF_D1(DEF)       "Downwards steps in elastic el. demand, relative data format";
SET DEF_U1(DEF)       "Upwards steps in elastic el. demand, relative data format";
SET DEF_D2(DEF)       "Downwards steps in elastic el. demand, absolute Money and MW-incremental data format";
SET DEF_U2(DEF)       "Upwards steps in elastic el. demand, absolute Money and MW-incremental data format";
SET DEF_D3(DEF)       "Downwards steps in elastic el. demand, absolute Money and fraction of nominal demand data format";
SET DEF_U3(DEF)       "Upwards steps in elastic el. demand, absolute Money and fraction of nominal demand data format";
SET DHF               "Steps in elastic heat demand";
SET DHF_D1(DHF)       "Downwards steps in elastic heat demand, relative data format";
SET DHF_U1(DHF)       "Upwards steps in elastic heat demand, relative data format";
SET DHF_D2(DHF)       "Downwards steps in elastic heat demand, absolute Money and MW-incremental data format";
SET DHF_U2(DHF)       "Upwards steps in elastic heat demand, absolute Money and MW-incremental data format";
SET DHF_D3(DHF)       "Downwards steps in elastic heat demand, absolute Money and fraction of nominal demand data format";
SET DHF_U3(DHF)       "Upwards steps in elastic heat demand, absolute Money and fraction of nominal demand data format";

SET MPOLSET           "Emission and other policy data";
SET ECONSET           "Set for econ"  !! todo
SET ECONSETCATEGORY   "Set for econ"  !! todo

* Internal set IGGGALIAS may be used in the $included data files:
ALIAS(GGG,IGGGALIAS);
* Internal set IGALIAS may be used in the $included data files:
ALIAS(G,IGALIAS);
* Set CCCRRRAAAALIAS may be used in the $included data files:
ALIAS(CCCRRRAAA,CCCRRRAAAALIAS);

* ACRONYMS:
* ACRONYMS for technology types
* Each of the following ACRONYMS symbolise a technology type.
* They correspond in a one-to-one way with the internal sets IGCND, IGBRP etc. below.
* They should generally not be changed.
* New technology types may be added only if also code specifying their properties are added.
ACRONYMS  GCND, GBPR, GEXT, GHOB, GETOH, GHSTO, GESTO, GHSTOS, GESTOS, GHYRS, GHYRR, GWND, GSOLE, GSOLH, GWAVE, GHS;

* ACRONYMS for user defined fuels will be given as part of file FFF.inc
* ACRONYMS for other purposes are defined in ACRONYMS.inc

*-------------------------------------------------------------------------------
*----- Definitions of SETS and ACRONYMS that are given in the $included files:
*-------------------------------------------------------------------------------
* Printing of data to the list file controlled by %ONOFFDATALISTING% and %ONOFFCODELISTING%
* (see file balgams.opt):


* Printing of data to the list file controlled by %ONOFFDATALISTING% and %ONOFFCODELISTING%
* (see file balgams.opt):
%ONOFFCODELISTING%

*-------------------------------------------------------------------------------
*--- End: Definitions of SETS and ACRONYMS that are given in the $included files
*-------------------------------------------------------------------------------

SET IS3(S)     "Balbase3: present season simulated; other models: identical to S";
SET IS3_NEXT(S) "Present seasons and  next season not simulated; if rolling seasons not activated  identical to S";
SET IS3_ONLYNEXT(S) "Next season not simulated; if rolling seasons not activated identical to S";
SET IS33(S,S)  "Mapping of S (first index) to the following S (second index)";

*-------------------------------------------------------------------------------
*----- Definitions of SETS and ALIASES that are needed for data entry:
*-------------------------------------------------------------------------------

* Duplication of sets for describing electricity exchange between regions:
ALIAS (C,IC);
ALIAS (RRR,IRRRE,IRRRI);
ALIAS (IR,IRE,IRI);
ALIAS (IA,IAE,IAI);
* Duplication of sets for fuel.
ALIAS (FFF,IFFFALIAS);
ALIAS (FFF,IFFFALIAS2);

* Duplication of sets for seasons and hours:
ALIAS (YYY,IYYYALIAS);
ALIAS (YYY,IYYYALIAS2);
ALIAS (Y,IYALIAS);
ALIAS (Y,IYALIAS2);
ALIAS (SSS,ISSSALIAS);
ALIAS (TTT,ITTTALIAS);
ALIAS (S,ISALIAS,ISALIAS2,ISALIAS3,IS3LOOPSET);
ALIAS (T,ITALIAS,ITALIAS2,ITALIAS3);


*-------------------------------------------------------------------------------
*----- End: Definitions of SETS and ALIASES that are needed for data entry:
*-------------------------------------------------------------------------------


*-------------------------------------------------------------------------------
* The choice of model made in the balopt.opt fil is checked here,
* and basic sets concerning time within the year are reconstructed accordingly if needed:

$ifi %bb3%==yes $KILL T
$ifi %bb3%==yes SET T(TTT)          /T001*T168/;
$ifi %bb3%==yes $KILL TWORKDAY
$ifi %bb3%==yes $KILL TWEEKEND
$ifi %bb3%==yes SET TWORKDAY(TTT)   /T001*T120/;
$ifi %bb3%==yes SET TWEEKEND(TTT)   /T121*T168/;
*-------------------------------------------------------------------------------


*------------------------------------------------------------------------------
* End: Declaration of internal sets
*------------------------------------------------------------------------------


*------------------------------------------------------------------------------
* Declaration and definition of numerical data: PARAMETERS and SCALARS:
*------------------------------------------------------------------------------


*------------------------------------------------------------------------------
*---- Technology data: ---------------------------------------------------------
*------------------------------------------------------------------------------
PARAMETER GDATA(GGG,GDATASET)    "Technologies characteristics";


*-------------------------------------------------------------------------------
* Definitions of internal sets relative to technologies,
* The sets are defined based on information in PARAMETER GDATA.

* The following are convenient internal subsets of generation technologies:

SET IGCND(G)               "Condensing technologies";                           !! Corresponding to acronym GCND
SET IGBPR(G)               "Back pressure technologies";                        !! Corresponding to acronym GBPR
SET IGEXT(G)               "Extraction technologies";                           !! Corresponding to acronym GEXT
SET IGHOB(G)               "Heat-only boilers";                                 !! Corresponding to acronym GHOB
SET IGHS(G)				   "Heat savings";										!! Corresponding to acronym GHS
SET IGETOH(G)              "Electric heaters, heatpumps, electrolysis plants";  !! Corresponding to acronym GETOH
SET IGHSTO(G)              "Intra-seasonal heat storage technologies";          !! Corresponding to acronym GHSTO
SET IGHSTOS(G)             "Inter-seasonal heat storage technologies";          !! Corresponding to acronym GHSTOS
SET IGHSTOALL(G)           "All heat storage technologies (intra- plus inter-seasonal)";
SET IGESTO(G)              "Intra-seasonal electricity storage technologies";   !! Corresponding to acronym GESTO
SET IGESTOS(G)             "Inter-seasonal electricity storage technologies";   !! Corresponding to acronym GESTOS
SET IGESTOALL(G)           "All electricity storage technologies (intra- plus inter-seasonal)";
SET IGHYRS(G)              "Hydropower with reservoir";                         !! Corresponding to acronym GHYRS
SET IGHYRR(G)              "Hydropower run-of-river no reservoir";              !! Corresponding to acronym GHYRR
SET IGWND(G)               "Wind power technologies";                           !! Corresponding to acronym GWND
SET IGSOLE(G)              "Solar electrical power technologies";               !! Corresponding to acronym GSOLE
SET IGSOLH(G)              "Solar heat technologies";                           !! Corresponding to acronym GSOLH
SET IGVRE(G)                            "VRE technologies";
SET IGWAVE(G)              "Wave power technologies";                           !! Corresponding to acronym GWAVE
SET IGHH(G)                "Technologies generating heat-only";
SET IGHHNOSTO(G)           "Technologies generating heat-only, except storage";
SET IGNOTETOH(G)           "Technologies excluding electric heaters, heat pumps,electrolysis plants";
SET IGKH(G)                "Technologies with capacity specified on heat";
SET IGKHNOSTO(G)           "Technologies with capacity specified on heat, except storage";
SET IGKE(G)                "Technologies with capacity specified on electricity";
SET IGKENOSTO(G)           "Technologies with capacity specified on electricity, except storage";
SET IGDISPATCH(G)          "Dispatchable technologies";
SET IGEE(G)                "Technologies generating electricity only";
SET IGEENOSTO(G)           "Technologies generating electricity only, except storage (but includes hydro)";
SET IGKKNOWN(G)            "Technoloies for which the capacity is specified by the user";
SET IGKFIND(G)             "Technologies for which the capacity is found by algorithm as endogenous investments";
SET IGEH(G)                "Technologies generating electricity and heat";
SET IGE(G)                 "Technologies generating electricity";
SET IGH(G)                 "Technologies generating heat";
SET IGBYPASS(G)            "Technologies that may apply turbine bypass mode (subject to option bypass)";
SET IWATERTANK(G)          "Water tank intra-seasonal LARGE heat storage technology"; !! Corresponding to acronym WATERTANK
SET IPIT(G)                "Pit inter-seasonal heat storage technology";        !! Corresponding to acronym PIT
SET IHEATPUMP(G)           "Heatpump technology";                               !! Corresponding to acronym HEATPUMP
SET IHEATPUMPAIR(G)        "Air source heat pump technolgy";         !! Corresponding to acronym HEATPUMP_AIR
SET IHEATPUMPEXCESSHEAT(G) "Excess heat source heat pump technolgy"; !! Corresponding to acronym HEATPUMP_EXCESSHEAT
SET IHEATPUMPGROUND(G)     "Ground source heat pump technolgy";      !! Corresponding to acronym HEATPUMP_GROUND
SET IGHNOWT(G)             "Technologies that are not allowed to load specifically water tanks";
SET ILINKSTO(G,G)          "1st set: Heat storage, 2nd set: technologies allowed to load the storage";


*-------------------------------------------------------------------------------
*----- Any internal sets assignments for addon to be placed here: --------------
*-------------------------------------------------------------------------------
* NOTE: When making new generation technology types. Some add-ons may already
* be using values of GDATA(G,'GDTYPE'). Check addons referenced here to maximize
* consistency and avoid conflicts. It is encouraged to avoid using the '-' set
* operator and instead use the '+' operator for compound assignments.
* NOTE: isetdecdef.inc is loaded later


*-------------------------------------------------------------------------------
*----- End: Any internal sets assignments for addon to be placed here ----------
*-------------------------------------------------------------------------------

*-------------------------------------------------------------------------------
*---- End: Technology data -----------------------------------------------------
*-------------------------------------------------------------------------------

* Printing of data to the list file controlled by %ONOFFDATALISTING% and %ONOFFCODELISTING%:
%ONOFFDATALISTING%

PARAMETER GKFX(YYY,AAA,GGG)    "Capacity of exogenously given generation technologies (MW except for storages, where it is MWh)";
* Printing of data to the list file controlled by %ONOFFDATALISTING% and %ONOFFCODELISTING%:
%ONOFFCODELISTING%

*-------------------------------------------------------------------------------
*---- Declaration of parameters for "export_results"  -----------------------------------------------
*-------------------------------------------------------------------------------
* Data for handling of annual hydro constraints in future runs:
PARAMETER HYRSG(YYY,AAA,SSS)        "Water (hydro) generation quantity of the seasons to be transferred to future runs (MWh)";
PARAMETER VHYRS_SL(YYY,AAA,SSS)       "To be saved for comparison with BB1/BB2 solution value for VHYRS_S.L (initial letter is V although declared as a parameter) (MWh)";
PARAMETER WATERVAL(YYY,AAA,SSS)     "Water value (in input Money) to be transferred to future runs (input-Money/MWh)";
PARAMETER VHYRS_STL(YYY,AAA,SSS,TTT)  "Hourly hydro storage level (MWh)";
* Data for handling investments in future runs:
PARAMETER GKACCUMNET(YYY,AAA,GGG) "Resulting technology capacity development at end of (ULTimo) previous (i.e., start of current) year (MW) (MWh for storage) to be transferred to future runs";
PARAMETER XKACCUMNET(YYY,IRRRE,IRRRI) "Resulting transmission capacity development at end (MISSING: minus any decommissioning of them due to lifetime expiration) this BB4, at end of previous (i.e., available at start of current) year (MW) to be transferred to future runs";

* Data for handling storage
PARAMETER ESTOVOLTS(YYY,AAA,GGG,SSS,TTT) "Inter-seasonal Electricity storage contents at beginning of time segment (MWh) to be transferred to future runs (MWh)";
PARAMETER HSTOVOLTS(YYY,AAA,GGG,SSS,TTT) "Inter-seasonal Heat storage contents at beginning of time segment (MWh) to be transferred to future runs (MWh)";
PARAMETER ESTOVOLT(YYY,AAA,GGG,SSS,TTT) "Intra-seasonal Electricity storage contents at beginning of time segment (MWh) to be transferred to future runs (MWh)";
PARAMETER HSTOVOLT(YYY,AAA,GGG,SSS,TTT) "Intra-seasonal Heat storage contents at beginning of time segment (MWh) to be transferred to future runs (MWh)";
PARAMETER ESTOLOADT(YYY,AAA,GGG,SSS,TTT) "Intra-seasonal electricity storage loading to be transferred to future runs (MW)";
PARAMETER ESTOLOADTS(YYY,AAA,GGG,SSS,TTT) "Inter-seasonal electricity storage loading to be transferred to future runs (MW)";;
PARAMETER HSTOLOADT(YYY,AAA,GGG,SSS,TTT)  "Intra-seasonal heat storage loading to be transferred to future runs (MW)";
PARAMETER HSTOLOADTS(YYY,AAA,GGG,SSS,TTT) "Inter-seasonal heat storage loading to be transferred to future runs (MW)";
PARAMETER ESTOVOLTSVAL(YYY,AAA,GGG,SSS,TTT) "Inter-seasonal Electricity storage content  value (in input money) to be transferred to future runs (input-Money/MWh)";
PARAMETER HSTOVOLTSVAL(YYY,AAA,GGG,SSS,TTT) "Inter-seasonal Heat storage content value (in input money) to be transferred to future runs (input-Money/MWh)";
PARAMETER ESTOVOLTVAL(YYY,AAA,GGG,SSS,TTT) "Intra-seasonal Electricity storage content  value (in input money) to be transferred to future runs (input-Money/MWh)";
PARAMETER HSTOVOLTVAL(YYY,AAA,GGG,SSS,TTT) "Intra-seasonal Heat storage content value (in input money) to be transferred to future runs (input-Money/MWh)";

* Data for handling remaining energy dispatch
PARAMETER  DE_T(YYY,RRR,SSS,TTT)                 "Electricity demand (MW) to be transferred to future runs";
PARAMETER  DH_T(YYY,AAA,SSS,TTT)                 "Heat demand (MW) to be transferred to future runs";
PARAMETER  GE_T(YYY,AAA,GGG,SSS,TTT)               "Electricity generation (MW)  to be transferred to future runs";
PARAMETER  GH_T(YYY,AAA,GGG,SSS,TTT)               "Heat generation (MW)  to be transferred to future runs";
PARAMETER  GF_T(YYY,AAA,GGG,SSS,TTT)               "Fuel consumption rate (MW), existing units  to be transferred to future runs";
PARAMETER  X_T(YYY,IRRRE,IRRRI,SSS,TTT)          "Electricity export from region IRRRE to IRRRI to be transferred to future runs (MW)";

*Fuel use
PARAMETER F_T(YYY,CCCRRRAAA,FFF,SSS,TTT) "Aggregated fuel use by year, season, T, geography and fuel to b transferred to future runs (GJ)"

*Fuel price
PARAMETER FUELPRICE_EXC(YYY,AAA,FFF)             "Fuel prices to be transferred to future runs(Money/GJ)";

*-------------------------------------------------------------------------------
*---- End: Declaration of parameters for "export_results"  -----------------------------------------------
*-------------------------------------------------------------------------------

* All remaining (cf. ... .inc above) data files af included from the following file
$ifi     exist "bb4datainc.inc" $include                   "bb4datainc.inc";
$ifi not exist "bb4datainc.inc" $include  "../../base/model/bb4datainc.inc";

* UPS! Forgot DOL! TODO
*GKNMAX(YYY,AAA,GGG)$((NOT Y(YYY)) OR (NOT IA(AAA))) = INF;    Presently not implemented.
GKRATE(IA,G,S)$(GKRATE(IA,G,S) EQ 1) = 0; !! Should give no reduction in size unless the data files does not exploit that default value is 1.

* The two specifications of fuel type 'FDACRONYM' and 'FDNB', have relative merits.
* Under most circumstances 'FDACRONYM' is preferable, because it is more transparent.
* If 'FDACRONYM' can be used, provide no data for 'FDNB' in datafile, and vice versa.
* Use only 'FDACRONYM' in the remaining code:
FDATA(FFF,'FDACRONYM')$(NOT FDATA(FFF,'FDACRONYM')) = FDATA(FFF,'FDNB');

* No need to continue if there are errors
$if not errorfree $abort "Balmorel processing aborted after inclusion of file bb4datainc.inc due to data errors";

* ------------------------------------------------------------------------------

IS33(S,ISALIAS) = YES$(ORD(ISALIAS) EQ (ORD(S)+1));
IS33(S,ISALIAS)$((ORD(S) EQ CARD(S)) AND (ORD(ISALIAS) EQ 1)) = YES; !! CIRCULAR ADDED


* The following sets concern combination technologies.

* (Text and assignment of technology related subsets in file dataincbb4.inc:)
* The sets:
* IGCND,IGBPR,IGEXT,IGHOB,IGETOH,IGHSTO,IGESTO,IGHSTOS,IGESTOS,IGHYRS,IGHYRR,IGWND,IGSOLE,IGSOLH,IGWAVE
* are directly extracted from GDATA(G,'GDTYPE') and are used to reference
* technology types.
*
* IGHH and IGEE are used in the balance equations and for output control.
* IGHHNOSTO and IGEENOSTO is not currently used for anything.
*
* IGNOTETOH is used for O&M cost in the objective function, in the balance
* equation, in heat storage balance equations and in various output functions.
* IGKH and IGKE are used for capacity restrictions and for certain output files.
* IGKHNOSTO and IGKENOSTO are used for output.
* IGDISPATCH is used capacity restrictions and output.
* IGKKNOWN is used to exclude investment options.
* IGKFIND is used to single out investment options.
* IGEH is used for CHP specific taxes.
* IGE and IGH are used all over.

* The sets are defined based on information in PARAMETER GDATA.

* The specifications of technology type 'GDTYPE' in GDATA may use an acronym or a number.
* Under most circumstances an acronym is preferable, the list is given above.
* If an acronym can not be used, use the numbers consistently as seen below.


   IGCND(G)    = YES$(GDATA(G,'GDTYPE') EQ GCND);
   IGBPR(G)    = YES$(GDATA(G,'GDTYPE') EQ GBPR);
   IGEXT(G)    = YES$(GDATA(G,'GDTYPE') EQ GEXT);
   IGHOB(G)    = YES$(GDATA(G,'GDTYPE') EQ GHOB);
   IGETOH(G)   = YES$(GDATA(G,'GDTYPE') EQ GETOH);
   IGHSTO(G)   = YES$(GDATA(G,'GDTYPE') EQ GHSTO);
   IGHSTOS(G)  = YES$(GDATA(G,'GDTYPE') EQ GHSTOS);
   IGESTO(G)   = YES$(GDATA(G,'GDTYPE') EQ GESTO);
   IGESTOS(G)  = YES$(GDATA(G,'GDTYPE') EQ GESTOS);
   IGHYRS(G)   = YES$(GDATA(G,'GDTYPE') EQ GHYRS);
   IGHYRR(G)   = YES$(GDATA(G,'GDTYPE') EQ GHYRR);
   IGWND(G)    = YES$(GDATA(G,'GDTYPE') EQ GWND);
   IGSOLE(G)   = YES$(GDATA(G,'GDTYPE') EQ GSOLE);
   IGSOLH(G)   = YES$(GDATA(G,'GDTYPE') EQ GSOLH);
   IGWAVE(G)   = YES$(GDATA(G,'GDTYPE') EQ GWAVE);
   IGHS(G)	   = YES$(GDATA(G,'GDTECHGROUP') EQ HEAT_SAVING);


* Assignments of IGESTO, IGESTOS, IGHSTO and IGHSTOS may be changed if option stointers has a non-default value.
$ifi "%stointers%"=="all"  IGESTOS(IGESTO) = YES; IGHSTOS(IGHSTO) = YES;
$ifi "%stointers%"=="all"  IGESTO(IGESTO) = NO;   IGHSTO(IGHSTO) = NO;
$ifi "%stointers%"=="none" IGESTO(IGESTOS) = YES; IGHSTO(IGHSTOS) = YES;
$ifi "%stointers%"=="none" IGESTOS(IGESTOS) = NO; IGHSTOS(IGHSTOS) = NO;

*---------------
* The specifications of technology type 'GDTECHGROUP' in GDATA may use an acronym or a number.
* Under most circumstances an acronym is preferable, the list is given above.
* If an acronym can not be used, use the numbers consistently as seen below.


   IWATERTANK(G)= YES$(GDATA(G,'GDTECHGROUP') EQ WATERTANK);
   IPIT(G)      = YES$(GDATA(G,'GDTECHGROUP') EQ PIT);
   IHEATPUMP(G) = YES$(GDATA(G,'GDTECHGROUP') EQ HEATPUMP);

*-------------------------

   IGHHNOSTO(G) = NO;   IGHHNOSTO(IGHOB)   = YES;  IGHHNOSTO(IGSOLH)= YES;

   IGHSTOALL(G) =       IGHSTO(G)
                         +IGHSTOS(G);

   IGHH(G)      =       IGHHNOSTO(G)
                         +IGHSTOALL(G);

   IGKHNOSTO(G)     =   IGETOH(G)
                         +IGHHNOSTO(G);

   IGKH(G)          =   IGKHNOSTO(G)
                         +IGHSTOALL(G);

   IGEENOSTO(G)     =   IGCND(G)     !! In contrast to heat related technologies above,
                         +IGHYRS(G)  !! with elec related technologies a more enumeration approach is taken
                         +IGHYRR(G)  !! for illustrative purposes
                         +IGWND(G)
                         +IGSOLE(G)
                         +IGWAVE(G);

   IGEE(G)          =   IGCND(G)
                         +IGHYRS(G)
                         +IGHYRR(G)
                         +IGWND(G)
                         +IGSOLE(G)
                         +IGWAVE(G)
                         +IGESTO(G)
                         +IGESTOS(G);

   IGVRE(G)                     =       IGWND(G)
                                                + IGSOLE(G);

   IGESTOALL(G) =       IGESTO(G)
                         +IGESTOS(G);

   IGKE(G)          =   IGCND(G)
                         +IGBPR(G)
                         +IGEXT(G)
                         +IGESTO(G)
                         +IGESTOS(G)
                         +IGHYRS(G)
                         +IGHYRR(G)
                         +IGWND(G)
                         +IGSOLE(G)
                         +IGWAVE(G);

   IGKENOSTO(G)     =   IGKE(G)
                         -IGESTO(G)
                         -IGESTOS(G);

   IGNOTETOH(G)= NOT IGETOH(G);

   IGEH(G) = IGBPR(G)+IGEXT(G)+IGETOH(G);
   IGE(G)=IGEE(G)+IGEH(G);
   IGH(G)=IGHH(G)+IGEH(G);

*-----------------------

   IGDISPATCH(G)    =   IGCND(G)
                         +IGBPR(G)
                         +IGEXT(G)
                         +IGHOB(G)
                         +IGESTO(G)
                         +IGESTOS(G)
                         +IGHSTO(G)
                         +IGHSTOS(G)
                         +IGETOH(G)
                         +IGHYRS(G);

   IGKFIND(G)  = YES$(GDATA(G,'GDKVARIABL') EQ 1);
   IGKKNOWN(G) = NOT IGKFIND(G);

$ifi not %bypass%==yes   IGBYPASS(G) = NO;
$ifi %bypass%==yes       IGBYPASS(IGBPR)$GDATA(IGBPR,'GDBYPASSC') = YES;
$ifi %bypass%==yes       IGBYPASS(IGEXT)$GDATA(IGEXT,'GDBYPASSC') = YES;

*-------------------------------------------------------------------------------
*----- Any internal sets assignments for addon to be placed here: --------------
*-------------------------------------------------------------------------------
* NOTE: When making new generation technology types. Some add-ons may already
* be using values of GDATA(G,'GDTYPE'). Check addons referenced here to maximize
* consistency and avoid conflicts. It is encouraged to avoid using the '-' set
* operator and instead use the '+' operator for compound assignments.

$include "../../base/addons/_hooks/isetdecdef.inc"


*-------------------------------------------------------------------------------
*----- End: Any internal sets assignments for addon to be placed here ----------
*-------------------------------------------------------------------------------

*-------------------------------------------------------------------------------
*---- Investments: --------------------------------------------------------------
*-------------------------------------------------------------------------------

*-------------------------------------------------------------------------------
*---- Miscellaneous ------------------------------------------------------------
*-------------------------------------------------------------------------------

* SCALAR OMONEY specifies output currency name and its exchange rate to input currency.
* Example of declaration:  "SCALAR OMONEY "EUR07" / 1 /;".
* Since the text string holding the output currency is part of the declaration,
* the declaration is not given here in Balmorel.gms but in the included file.
* (For this reason you can not here apply the "Semislash-idea".)
* It is advised to add a comment in the data file stating what the input currency is and to which year it refers.

*-------------------------------------------------------------------------------
*----- Any parameters for addon to be placed here: -----------------------------
*-------------------------------------------------------------------------------

* This file (if exists) contains:
* PARAMETER XHKFX(IAAAE,IAAAI)    "Initial heat transmission capacity between regions"
* PARAMETER XHINVCOST(IAAAE,IAAAI) "Investment cost in new heat transmission cap"
* PARAMETER XHCOST(IAAAE,IAAAI)    "Heat transmission cost between countries"
* PARAMETER XHLOSS(IAAAE,IAAAI)    "Heat transmission loss between regions"

* Printing of data to the list file controlled by %ONOFFDATALISTING% and %ONOFFCODELISTING%:
%ONOFFDATALISTING%

SCALAR PENALTYQ  "Penalty on violation of equation (non-negative)";

SET YMODEL "YMODEL is a set used to derive the years from Y in each Balbase4 model";
ALIAS(YMODEL, IYMODEL4)
PARAMETER YMODELDELTA(YMODEL) "Number of years between a year and the preceding year represented in model Balbase4 ('number' means difference between the ord in Y)";
* Printing of data to the list file controlled by %ONOFFDATALISTING% and %ONOFFCODELISTING%:
%ONOFFCODELISTING%

*-------------------------------------------------------------------------------
*----- End: Any parameters for addon to be placed here -------------------------
*-------------------------------------------------------------------------------

*-------------------------------------------------------------------------------
* End: Declaration and definition of numerical data: PARAMETERS and SCALARS
*-------------------------------------------------------------------------------

* Omit non-relevant information wrt. geography for present models. Non-exhaustive list.
DE_VAR_T(RRR,DEUSER,SSS,TTT)$(not IR(RRR)) = 0;
DE_VAR_T(RRR,DEUSER,SSS,TTT)$(not IR(RRR)) = 0;
DH_VAR_T(AAA,DHUSER,SSS,TTT)$(not IA(AAA)) = 0;
X3FX_VAR_T(RRR,SSS,TTT)$(not IR(RRR)) = 0;
WND_VAR_T(AAA,SSS,TTT)$(not IA(AAA)) = 0;
SOLE_VAR_T(AAA,SSS,TTT)$(not IA(AAA)) = 0;
SOLH_VAR_T(AAA,SSS,TTT)$(not IA(AAA)) = 0;
WAVE_VAR_T(AAA,SSS,TTT)$(not IA(AAA)) = 0;
WTRRRVAR_T(AAA,SSS,TTT)$(not IA(AAA)) = 0;

*-------------------------------------------------------------------------------
* Declaration and definition of (additional) internal sets, aliases and parameters:
*-------------------------------------------------------------------------------

* Aliases relative to time:

ALIAS (S,ISALIAS);
ALIAS (T,ITALIAS);
ALIAS (Y,IYALIAS44);
ALIAS (Y,IY402);
SET IY411(Y)                "IY411 The years in current Balbase4 model";
SET IY410(Y)                "IY410 The years in the current Balbase4 model except the last year" ;
SET IY401(Y)                "IY401 The years in the current Balbase4 model except the first year" ;
SET IY411FIRST(Y)           "The first year in the current Balbase4 model";
SET IY411PREVY(Y,Y)         "For any given element in IY411 (index Y 1): the previous element in Y (index Y 2)";
SET IYFIRST(Y)              "The first year in Y";
IYFIRST(Y)$(ORD(Y) EQ 1) = YES;



*-------------------------------------------------------------------------------
* Application of default data:
*-------------------------------------------------------------------------------

* GOMVCOSTO,GOMVCOSTIN, GOMFCOST and GINVCOST are given the default values in GDATA unless non-zero values or EPS is specified in the data file:
GOMVCOSTO(IA,G)$((NOT GOMVCOSTO(IA,G)) AND (SUM(Y,GKFX(Y,IA,G)) OR AGKN(IA,G))) = GDATA(G,'GDOMVCOST0');
GOMVCOSTIN(IA,G)$((NOT GOMVCOSTIN(IA,G)) AND (SUM(Y,GKFX(Y,IA,G)) OR AGKN(IA,G))) = GDATA(G,'GDOMVCOSTIN');
GOMFCOST(IA,G)$((NOT GOMFCOST(IA,G)) AND (SUM(Y,GKFX(Y,IA,G)) OR AGKN(IA,G))) = GDATA(G,'GDOMFCOST0');
GINVCOST(IA,G)$((NOT GINVCOST(IA,G)) AND (SUM(Y,GKFX(Y,IA,G)) OR AGKN(IA,G))) = GDATA(G,'GDINVCOST0');

*-------------------------------------------------------------------------------
* End of: Application of default data
*-------------------------------------------------------------------------------

* Time aggregation:
$ifi %timeaggr%==yes  $include '../../base/addons/timeaggregation/timeaggr.inc';

* The following relates technology and fuel:
SET IGF(GGG,FFF)   "Relation between technology type and fuel type";

* The following relates technology and tech group:
SET IGTECH_GROUP(GGG,TECH_GROUP) "Relation between technology and tech group";

* The following relates technology and user group:
SET IGDEUSER(G,DEUSER) "Relation between distributed generation technologies and user group for electricity";

SET IRESE(DEUSER)  "Associate DEUSER with RESE user";
SET IIND(DEUSER)  "Associate DEUSER with PII user";

* Internal scalars:
SCALAR ILOOPBREAK     "Scalar used as binary number to break any loop function";
SCALAR IFIRSTYEARNEXTBB4 "First year in the next Balbase4 model";

*------------------------------------------------------------------------------
* Internal sets:

SET IAGKFX(Y,AAA,G)    "Area, technology with positive endogenous capacity current simulation year";
SET IXKN(Y,IRRRE,IRRRI)  "Pair of regions that may get new transmission capacity, yearly dependent";

* Specification of where new endogenous generation capacity may be located:

SET IAGKN(AAA,G) "Area, technology where technology may be invested based on AGKN and implicit year independent constraints from FKPOT";
SET IAGKNY(Y,AAA,G) "Area, technology where technology may be invested based on IAGKN and implicit constraint from first investment year";

SET IGKN_ES(GGG)         "Technologies lines whose cost depends on economy of scale";
SET IXKN_ES(IRRRE,IRRRI) "Transmission lines whose cost depends on economy of scale";

SET IXK_HASORPOT(Y,IRRRE,IRRRI) "Transmission lines with existing or potentially invested capacity current year";
SET IAGK_HASORPOT(Y,AAA,G) "Technologies with existing or potentially invested capacity current year";
SET IGDECOMEXOPOT(Y,AAA,G) "Technologies with potential exogenous capacity to be decommissioned";

SET IPLUSMINUS "Violation of equation"  /IPLUS Violation of equation upwards, IMINUS  Violation of equation downwards/;
* Note: When placed on the left hand side of the equation
* the sign to the IMINUS and IPLUS terms should be - and +, respectively.
* This way the sign and the name will be intuitively consistent in equation listings.

*------------------------------------------------------------------------------
* Internal parameters and settings:
*------------------------------------------------------------------------------
*The following corrects the economic values in input data (defined in money/MWh) to match the relative size of T in the objective function, in case the size of T does not correspond to 1 hour
SCALAR IHOURFRAC "Weight of T with respect to 1 hour (if T means 1 hour, then IHOURFRAC is 1, if T means 0.5 hours, IHOURFRAC is 0.5, etc.)";
IHOURFRAC=8736/(CARD(TTT)*CARD(SSS));

*Initializing the set IGDECOMEXOPOT in case the add-on DECOM is not activated
IGDECOMEXOPOT(Y,IA,G)=0;

*Initializing the sets IGKN_ES and IXKN_ES in case the add-on OFFSHOREGRID is not activated
$ifi not %OFFSHOREGRID%==yes IGKN_ES(G)=0;
$ifi not %OFFSHOREGRID%==yes IXKN_ES(IRRRE,IRRRI)=0;

*Initializing the sets IHYDROGEN in case the add-on hydrogen is not activated
$ifi not %HYDROGEN%==yes SET IHYDROGEN(GGG);
$ifi not %HYDROGEN%==yes IHYDROGEN(G)=0;

PARAMETER IWEIGHTY(Y)                  "Relative weight of the individual years in Y";
* Set the relative weight of the individual years in Y.
* Two ideas implemented here. Used according to option bb4weighty.
* Simple idea is to give equal weights:
$ifi "%bb4weighty%"=="same"      IWEIGHTY(Y) = 1;
* More complex weighting of the individual years (years in YYY but not in Y are shared between two nearest (first and last years double the shared weight contribution)):
$ifi "%bb4weighty%"=="shareYYY"  IWEIGHTY(Y)$(ORD(Y) EQ 1) = 1$(CARD(Y) EQ 1) + ((YVALUE(Y+1)-YVALUE(Y)-1)+1)$(CARD(Y) GT 1);
$ifi "%bb4weighty%"=="shareYYY"  IWEIGHTY(Y)$((ORD(Y) GT 1) AND (ORD(Y) LT CARD(Y))) = (YVALUE(Y) - YVALUE(Y-1) -1)/2  + (YVALUE(Y+1) - YVALUE(Y) -1)/2    +1;
$ifi "%bb4weighty%"=="shareYYY"  IWEIGHTY(Y)$((ORD(Y) EQ CARD(Y)) AND (CARD(Y) GT 1)) = ((YVALUE(Y)-YVALUE(Y-1)-1)+1);
* Unload IWEIGHTY for the output tool
execute_unload '%relpathModel%../output/temp/IWEIGHTY.gdx' IWEIGHTY;

PARAMETER IYHASANNUITYG(Y,Y,G)         "Binary parameter to establish whether the annuity of an investment of a technology made in Y (first index) should be paid in the time period Y (second index) (0,1)" ;
PARAMETER IYHASANNUITYX(Y,Y)           "Binary parameter to establish whether the annuity of an investment of a transmission line investment made in Y (first index) should be paid in the time period Y (second index) (0,1)";
PARAMETER IINVYEARG_LEFT(Y,Y,G)      "Remaining years of the lifetime of G of an investment made in Y (first index) at the beggining of Y (second index) (years)";
PARAMETER IINVYEARX_LEFT(Y,Y)        "Remaining years of the lifetime of a transmission line investment made in Y (first index) at the beggining of Y (second index) (years)";
PARAMETER IN_INV_G(Y,G)              "Number of investments made OF G within Y (fraction)";
PARAMETER IN_INV_X(Y)                "Number of investments made OF a transmission line within Y (fraction)";


*------------ Calculation of IYHASANNUITYG and IYHASANNUITYX to include/exclude the payment of the annuities---------------------
$ifi not %TechInvest%==yes  IYHASANNUITYG(IYALIAS,Y,IGKFIND)= 0;
$ifi not %TransInvest%==yes IYHASANNUITYX(IYALIAS,Y)= 0;

$ifi not %TechInvest%==yes $goto NO_TECH_INVESTMENTS
**GENERATION
LOOP(IGKFIND,
  LOOP(IYALIAS,
    LOOP(Y$(ORD(Y) EQ ORD(IYALIAS)),
      IINVYEARG_LEFT(IYALIAS,Y,IGKFIND)=GDATA(IGKFIND,'GDLIFETIME');
    );
  );
);

LOOP(IGKFIND,
  LOOP(IYALIAS,
    ILOOPBREAK=0;
    IN_INV_G(IYALIAS,IGKFIND)=ROUND(IWEIGHTY(IYALIAS)/GDATA(IGKFIND,'GDLIFETIME'));
*Correction of IN_INV_G
      IF (IN_INV_G(IYALIAS,IGKFIND) EQ 0,
        IN_INV_G(IYALIAS,IGKFIND)=1;
      );
      LOOP(Y$(ORD(Y) GE ORD(IYALIAS) AND (ILOOPBREAK EQ 0)),
*First year's annuity
        IF (ORD(Y) EQ ORD(IYALIAS),
          IYHASANNUITYG(IYALIAS,Y,IGKFIND)= 1;
          IF(IINVYEARG_LEFT(IYALIAS,Y,IGKFIND)*IN_INV_G(IYALIAS,IGKFIND) LE IWEIGHTY(Y),
            ILOOPBREAK=1;
          );
          IINVYEARG_LEFT(IYALIAS,Y+1,IGKFIND)$(ORD(Y) NE CARD(IYALIAS2))=GDATA(IGKFIND,'GDLIFETIME')*IN_INV_G(IYALIAS,IGKFIND)-IWEIGHTY(Y);
        );
*Remaining year's annuity
      IF (ORD(Y) GT ORD(IYALIAS),
        IF ( IINVYEARG_LEFT(IYALIAS,Y,IGKFIND) GT IWEIGHTY(Y) ,
          IYHASANNUITYG(IYALIAS,Y,IGKFIND)= 1;
            IINVYEARG_LEFT(IYALIAS,Y+1,IGKFIND)$(ORD(Y) NE CARD(IYALIAS2))=IINVYEARG_LEFT(IYALIAS,Y,IGKFIND)-IWEIGHTY(Y);
          );
          IF ((IINVYEARG_LEFT(IYALIAS,Y,IGKFIND) GE IWEIGHTY(IYALIAS)/2) AND (IINVYEARG_LEFT(IYALIAS,Y,IGKFIND) LE IWEIGHTY(Y)) ,  !!Assumption: if the reamining years are more ore equal than half of IWEIGHTY, then the technology is in in this snapshot
            IYHASANNUITYG(IYALIAS,Y,IGKFIND)= 1;
            ILOOPBREAK=1;
          );
          IF ((IINVYEARG_LEFT(IYALIAS,Y,IGKFIND) LT IWEIGHTY(IYALIAS)/2) AND (IINVYEARG_LEFT(IYALIAS,Y,IGKFIND) LE IWEIGHTY(Y)) , !!Assumption: if the reamining years are less than half of IWEIGHTY, then the technology is out in this snapshot
            IYHASANNUITYG(IYALIAS,Y,IGKFIND)= 0;
            ILOOPBREAK=1;
          );
        );
      );
  );
);
$label NO_TECH_INVESTMENTS

$ifi not %TransInvest%==yes $goto NO_TRANS_INVESTMENTS
** TRANSMISSION LINES
LOOP(IYALIAS,
  LOOP(Y$(ORD(Y) EQ ORD(IYALIAS)),
    IINVYEARX_LEFT(IYALIAS,Y)=LIFETIME_X;
  );
);

LOOP(IYALIAS,
  ILOOPBREAK=0;
  IN_INV_X(IYALIAS)=ROUND(IWEIGHTY(IYALIAS)/LIFETIME_X);
*Correction of inv
  IF ( IN_INV_X(IYALIAS) EQ 0,
    IN_INV_X(IYALIAS)=1;
  );
  LOOP(Y$(ORD(Y) GE ORD(IYALIAS) AND (ILOOPBREAK EQ 0)),

*First year's annuity
    IF ( ORD(Y) EQ ORD(IYALIAS),
      IYHASANNUITYX(IYALIAS,Y)= 1;
      IF(IINVYEARX_LEFT(IYALIAS,Y)*IN_INV_X(IYALIAS) LE IWEIGHTY(Y),
      ILOOPBREAK=1;
      );
      IINVYEARX_LEFT(IYALIAS,Y+1)$(ORD(Y) NE CARD(IYALIAS2))=LIFETIME_X*IN_INV_X(IYALIAS)-IWEIGHTY(Y);
    );
*Remaining year's annuity
    IF ( ORD(Y) GT ORD(IYALIAS),
      IF ( IINVYEARX_LEFT(IYALIAS,Y) GT IWEIGHTY(Y) ,
        IYHASANNUITYX(IYALIAS,Y)= 1;
        IINVYEARX_LEFT(IYALIAS,Y+1)$(ORD(Y) NE CARD(IYALIAS2))=IINVYEARX_LEFT(IYALIAS,Y)-IWEIGHTY(Y);
      );
      IF ( (IINVYEARX_LEFT(IYALIAS,Y) GE IWEIGHTY(Y)/2) AND (IINVYEARX_LEFT(IYALIAS,Y) LE IWEIGHTY(Y)) ,
        IYHASANNUITYX(IYALIAS,Y)= 1;
        ILOOPBREAK=1;
      );
      IF ( (IINVYEARX_LEFT(IYALIAS,Y) LT IWEIGHTY(Y)/2) AND (IINVYEARX_LEFT(IYALIAS,Y) LE IWEIGHTY(Y)) ,
        IYHASANNUITYX(IYALIAS,Y)= 0;
        ILOOPBREAK=1;
      );
    );
  );
);
$label NO_TRANS_INVESTMENTS
*------------ END of Calculation of the correction factor for the annuities---------------------

* Set GDCV value to one for those technologies with capacity defined on HEAT and that are not IGEXT so that their fuel consumption and O&M costs
* can be found using the same formula as for IGCND and IGEXT:
GDATA(IGBPR,'GDCV') = 1;
GDATA(IGHOB,'GDCV') = 1;
GDATA(IGETOH,'GDCV')  = 1;
GDATA(IGHSTO,'GDCV')  = 1;
GDATA(IGHSTOS,'GDCV') = 1;
GDATA(IGSOLH,'GDCV') = 1;

* Specifying the relation between technology type and fuel type in IGF:

IGF(G,FFF)=YES$(GDATA(G,'GDFUEL') EQ FDATA(FFF,'FDACRONYM'));

* Specifying the relation between technology type and tech group in IGTECH_GROUP:
IGTECH_GROUP(G,TECH_GROUP)=YES$(GDATA(G,'GDTECHGROUP') EQ TECH_GROUP_VALUE(TECH_GROUP));

* Specifying the relation between technology type and user group in IGDEUSER:
*IGDEUSER(G,DEUSER) = YES$SUM(TECH_GROUP$(TECHGROUP_DEUSER(TECH_GROUP,DEUSER) EQ 1), IGTECH_GROUP(G,TECH_GROUP));


