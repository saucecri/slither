"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.function import get_function_id
from slither.utils.myprettytable import MyPrettyTable

import sys
from slither.slither import Slither
from slither.utils.colors import yellow,magenta,blue

def run_indirect_writing_variables(self):

  for contract in self.contracts:
    print(blue(f"Analyzing {contract.name}"))

    # Get the variable
    for variable in contract.state_variables:

        for function in contract.functions:
            for elem in function.state_variables_written:
                if str(variable) in str(elem):
                    print(f"{str(variable)} being written in {function.name}")
        # Get the functions writing the variable

        functions_writing_variable = contract.get_functions_writing_to_variable(variable)
        len_functions_writing = len(functions_writing_variable)

            # Print the result
        print(magenta('The function writing {} are {}'.format(variable, [f.name for f in functions_writing_variable])))

            # Now I need to get the functions calling the primary functions, because indirectly they will also modify this variable, and so on until we get every level of indirection

        for function_writing_variable in functions_writing_variable:
            for reachable in function_writing_variable.reachable_from_functions:
                functions_writing_variable.append(reachable)  
            
        # We remove duplicates
        functions_writing_variable = list(dict.fromkeys(functions_writing_variable))
            
        # We prepare variable without the primary functions modifying variable and print
        # Every level of indirection is presented in the same print statement. Should I change that ?
        indirect_writing_variable = functions_writing_variable[len_functions_writing:]
        print(yellow('Indirect functions writing {} are {}'.format(variable, [ element.name for element in indirect_writing_variable])))



class IndirectWritingVariables(AbstractPrinter):

    ARGUMENT = "indirect-writing-variables"
    HELP = "Print the keccack256 signature of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#function-id"

    def output(self, _filename):
        txt = ''

        run_indirect_writing_variables(self)
        
        return self.generate_output(txt)
