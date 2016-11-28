#!/usr/bin/env python

from aiida.orm import Code, DataFactory
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')

###############################
# Set your values here
codename = '5qchem@lcmdlc2'
###############################

code = Code.get_from_string(codename)

# BaTiO3 cubic structure
alat = 4. # angstrom
cell = [[alat, 0., 0.,],
       [0., alat, 0.,],
       [0., 0., alat,],
       ]
s = StructureData(cell=cell)
s.append_atom(position=(2,2,2),symbols='Ti')
s.append_atom(position=(2,2.,0.),symbols='O')
s.append_atom(position=(2,0.,2),symbols='O')
s.append_atom(position=(0.,2,2),symbols='O')

parameters = ParameterData(dict={
    "CHARGE":"0",
    "THREADS":"1",
    "CPUS":"1",
    "MULTIPLICITY":"1",
    "BASIS":"6-31G",
    "JOB_TYPE":"SP",
    "BASIS_LINEAR_DEPENDENCE_THRESH":"6",
    "DFT_D":"FALSE",
    "MEM_STATIC":"240",
    "MEM_TOTAL":"2000",
    "METHOD":"HF",
    "SCF_ALGORITHM":"DIIS",
    "SCF_CONVERGENCE":"8",
    "SCF_GUESS":"SAD",
    "SCF_MAX_CYCLES":"50",
    "THRESH":"8",
    "UNRESTRICTED":"0",
    "XC_GRID":"1",
    "add_cell": False,
    })

#parameters = ParameterData(dict={
#"abbreviation": "aiida_calc",               # Short name for the computation
#  "title":        "AiiDA NWChem calculation", # Long name for the computation
#    "basis":                                    # Basis per chemical type
#        {
#                  "Ba": "library 6-31g",
#                        "Ti": "library 6-31g",
#                              "O":  "library 6-31g",
#                                  },
#          "task":         "scf",                      # Computation task
#            "add_cell":     True,                       # Include cell parameters?
#})

calc = code.new_calc(max_wallclock_seconds=3600,
            resources={"num_machines": 1})
calc.label = "A generic title"
calc.description = "A much longer description"

calc.use_structure(s)
calc.use_code(code)
calc.use_parameters(parameters)

calc.store_all()
print "created calculation with PK={}".format(calc.pk)
#calc.submit_test()
calc.submit()
