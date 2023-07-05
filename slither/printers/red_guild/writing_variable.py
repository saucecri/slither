"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output
import sys
from slither.slither import Slither
from slither.utils.colors import yellow,magenta,blue

class WritingVariable(AbstractPrinter):
    WIKI = "https://github.com/crytic/slither/wiki/Printer-documentation#constructor-calls"
    ARGUMENT = "writing-variable"
    HELP = "Print the unchecked-params"

    def output(self, _filename):
        res = ''

        result = run_writing_variable(self, '_reportingState')
        if type(result) != type(None):
                #print(f"RSULT: {result}")
            res = res.join(result)
        
        return self.generate_output(res)

def run_writing_variable(self, variable):

  for contract in self.contracts:
    print(blue(f"Analyzing {contract.name}"))

    # Get the variable
    var_a = contract.get_state_variable_from_name(variable)
    if var_a:
        # Get the functions writing the variable
        functions_writing_variable = contract.get_functions_writing_to_variable(var_a)
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
