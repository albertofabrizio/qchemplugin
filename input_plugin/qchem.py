# -*- coding: utf-8 -*-
import os
import shutil

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty

class QchemCalculation(JobCalculation):
    """
    Input plugin for QChem. This just creates a input from StructureData and
    parameters:
"""
    def _init_internal_params(self):
        super(QchemCalculation, self)._init_internal_params()

        # Name of the default output parser
        self._default_parser = 'qchem.QchemBaseParser'

        # Default input and output files
        self._DEFAULT_INPUT_FILE  = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'
        self._DEFAULT_ERROR_FILE  = 'aiida.err'

    @classproperty
    def _use_methods(cls):
        retdict = JobCalculation._use_methods
        retdict.update({
            "structure": {
               'valid_types': StructureData,
               'additional_parameter': None,
               'linkname': 'structure',
               'docstring': "A structure to be processed",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': "Parameters used to describe the calculation",
               },
            })
        return retdict

    def _prepare_for_submission(self,tempfolder,inputdict):
        import numpy as np

        try:
            struct = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("no structure is specified for this calculation")
        if not isinstance(struct, StructureData):
            raise InputValidationError("struct is not of type StructureData")

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("no code is specified for this calculation")

        atoms = struct.get_ase()

     
        parameters = inputdict.pop(self.get_linkname('parameters'), None)
        if parameters is None:
            parameters = ParameterData(dict={})
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")
        par = parameters.get_dict()

        charge= par.pop('CHARGE', '0')
        threads= par.pop('THREADS','1')
        cpus=par.pop ('CPUS','1')
        mult= par.pop(' MULTIPLICITY', '1')
        basis = par.pop('BASIS','6-31G')
        jobtype = par.pop('JOB_TYPE','SP')
        basis_lin_dep=par.pop('BASIS_LINEAR_DEPENDENCE_THRESH','6')
        dft_d=par.pop('DFT_D','FALSE')
        if dft_d == 'EMPIRICAL_GRIMME3':
            s6=par.pop('DFT_D3_S6','1000')
            s8=par.pop('DFT_D3_S8','1000')
            sr6=par.pop('DFT_D3_SR6','1000')
        static=par.pop('MEM_STATIC', '240')
        total=par.pop('MEM_TOTAL', '2000')
        method=par.pop('METHOD', 'HF')
        algorithm=par.pop('SCF_ALGORITHM', 'DIIS')
        convergence=par.pop('SCF_CONVERGENCE', '8')
        guess=par.pop('SCF_GUESS', 'SAD')
        cycles=par.pop('SCF_MAX_CYCLES', '50')
        threshold=par.pop('THRESH', '8')
        unrestricted=par.pop('UNRESTRICTED', '0')
        xc_grid=par.pop('XC_GRID', '1')
        add_cell = par.pop('add_cell',False)

        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(input_filename,'w') as f:
            f.write('$molecule\n')
            f.write(' {} {}\n'.format(charge,mult))
            for i,atom_type in enumerate(atoms.get_chemical_symbols()):
                f.write('    {} {} {} {}\n'.format(atom_type,
                                               atoms.get_positions()[i][0],
                                               atoms.get_positions()[i][1],
                                               atoms.get_positions()[i][2]))
            f.write('$end\n\n$rem\n')
            f.write(' BASIS = {}\n'.format(basis))
            f.write(' JOB_TYPE = {}\n'.format(jobtype))
            f.write(' BASIS_LINEAR_DEPENDENCE_THRESH = {}\n'.format(basis_lin_dep))
            f.write(' DFT_D = {}\n'.format(dft_d))
            if dft_d == 'EMPIRICAL_GRIMME3':
                f.write(' DFT_D3_S6 = {}\n'.format(s6))
                f.write(' DFT_D3_S8 = {}\n'.format(s8))
                f.write(' DFT_D3_SR6 = {}\n'.format(sr6))
            f.write(' MEM_STATIC = {}\n'.format(static))
            f.write(' MEM_TOTAL = {}\n'.format(total))
            f.write(' METHOD = {}\n'.format(method))
            f.write(' SCF_ALGORITHM = {}\n'.format(algorithm))
            f.write(' SCF_CONVERGENCE = {}\n'.format(convergence))
            f.write(' SCF_GUESS = {}\n'.format(guess))
            f.write(' SCF_MAX_CYCLES = {}\n'.format(cycles))
            f.write(' THRESH = {}\n'.format(threshold))
            f.write(' UNRESTRICTED = {}\n'.format(unrestricted))
            f.write(' XC_GRID = {}\n'.format(xc_grid))
            f.write('$end\n')
            f.flush()

        self._DEFAULT_INPUT_FILE  = 'aiida.in'
        self._default_commandline_params = ["-nt" , threads, "-np " , cpus, ]

        commandline_params = self._default_commandline_params

        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE,
                                  self._DEFAULT_ERROR_FILE]
        calcinfo.retrieve_singlefile_list = []

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = commandline_params
        codeinfo.stdin_name = self._DEFAULT_INPUT_FILE
        codeinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        codeinfo.stderr_name = self._DEFAULT_ERROR_FILE
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        return calcinfo

    def convert_to_uppercase(item_in_dict):
        """
        This method recursively goes through a dictionary
        and converts all the keys to uppercase.
        On the fly, it also converts the values (if strings) to upppercase
        """
       
        try:
            for key in item_in_dict.keys():
                item_in_dict[key.upper()] = convert_to_uppercase(item_in_dict.pop(key))
        except AttributeError:
            try:
                return item_in_dict.upper()
            except AttributeError:
                return item_in_dict
        return item_in_dict

