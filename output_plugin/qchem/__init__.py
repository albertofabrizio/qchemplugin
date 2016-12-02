# -*- coding: utf-8 -*-
from aiida.orm.data.parameter import ParameterData
from aiida.parsers.parser import Parser

class QchemBaseParser(Parser):

    def parse_with_retrieved(self,retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        output_path = None
        error_path  = None

        try:
            output_path, error_path = self._fetch_output_files(retrieved)
        except InvalidOperation:
            raise
        except IOError as e:
            self.logger.error(e.message)
            return False, ()

        if output_path is None and error_path is None:
            self.logger.error("No output files found")
            return False, ()

        self._get_output_nodes(output_path, error_path)

        return True, self._get_output_nodes(output_path, error_path)

    def _fetch_output_files(self, retrieved):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.

        :param retrieved: A dictionary of retrieved nodes, as obtained from the
          parser.
        """
        from aiida.common.datastructures import calc_states
        from aiida.common.exceptions import InvalidOperation
        import os

        # Check that the retrieved folder is there
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            raise IOError("No retrieved folder found")

        list_of_files = out_folder.get_folder_list()

        output_path = None
        error_path  = None

        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files:
            output_path = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_OUTPUT_FILE )
        if self._calc._DEFAULT_ERROR_FILE in list_of_files:
            error_path  = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_ERROR_FILE )

        return output_path, error_path


    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        with open(output_path) as f:
            lines = [x.strip('\n') for x in f.readlines()]

        result_dict = dict()
        trajectory = None
        icounter=0
        result_dict['HOMO (alpha/beta)']=[]
        result_dict['LUMO (alpha/beta)']=[]
        for line in lines:
            icounter += 1
            if ('Total energy in the final basis set' in line):
                result_dict['energy']=line.split()[8]
                continue
            if ('Dipole Moment (Debye)' in line):
                result_dict['dipole moment']=''.join(lines[icounter])
                continue
            if ('-- Virtual --' in line):
                result_dict['HOMO (alpha/beta)'].append(''.join(lines[icounter-3]).split()[-1])
                result_dict['LUMO (alpha/beta)'].append(''.join(lines[icounter]).split()[0])
                continue


        return [('parameters', ParameterData(dict=result_dict))]
