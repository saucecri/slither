"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.function import get_function_id
from slither.utils.myprettytable import MyPrettyTable

from deepdiff import DeepDiff
from pprint import pprint
import re

from slither.printers.red_guild.utils import get_reachable_functions_recursively, check_writing_assembly
from slither.slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import blue, green, yellow, red, magenta
from slither.core.declarations.solidity_variables import SolidityVariableComposed

class InheritedStateDesync(AbstractPrinter):

    ARGUMENT = "inherited-state-desync"
    HELP = "Print the keccack256 signature of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#function-id"

    def output(self, _filename):

        txt = ''

        run_inherited_state_desync(self)

        return self.generate_output(txt)



def run_inherited_state_desync(self):
    detector_results = []
    for contract in self.contracts:
        print(magenta(f"Analyzing {contract.name} contract"))
        # For each one of the inherited functions

        for inh_function in contract.functions_inherited:
            inh_function_id = get_function_id(inh_function.solidity_signature)
            
            # We go through the non_inherited ones to validate if they are overriding a function.
            for non_inh_func in contract.functions_declared:
                non_inh_function_id = get_function_id(non_inh_func.solidity_signature)
                
                # If sinatures and names are the same, then we know they are overriding one inherited function.
                if inh_function_id == non_inh_function_id and inh_function.name == non_inh_func.name:
                    diff_sol = None
                    diff_state = None
                    # If the expressions differ (lines of code )  between each other, then we know they are modifying something. If they are the same, we need to validate line by line to understand if there is any difference in both implementatons. 

                    if len(inh_function.expressions) == len(non_inh_func.expressions):
                        counter = 0 

                        for expression in inh_function.expressions:
                            # We validate each one of their expressions to capture the ones in which they differ.              
                            if expression != non_inh_func.expressions[counter]:

                                try:
                                    diff_sol, diff_state =  find_function_difference(inh_function, non_inh_func)
                                except:
                                    # We should never have a case like this, since if you are overriding s function, why would you be overriding it with an implementation that it's exactly as the inherited one ?
                                    diff_sol = None
                                    diff_state = None
                                    pass
                                # We  are only detecting one difference, maybe this should be improved to capture more than one.
                                break
                            else:
                                counter = counter + 1
                                
                    else:
                        try:
                            # Does it handle if one of diff_sol or diff_state is null?
                            diff_sol, diff_state = find_function_difference(inh_function, non_inh_func)
                        except:
                            diff_sol = None
                            diff_state = None
                            pass
                    
                    # I think that this case should be handled in some way, but cannot currently think on how the "solidity variables" may be important 
                    if diff_sol:
                        handle_results(diff_sol, False, non_inh_func.name)

                    if diff_state:

                        diff_vars = handle_results(diff_state, True, non_inh_func.name) 

                        results = []
                        reachable_func = {}
                        list_of_results_reachable = []
                        get_reachable_functions_recursively(contract, non_inh_func, results, reachable_func, list_of_results_reachable)
                        
                        # Now that we know which function is overriding the implementation, what we want to know is which variables are modified by this "functionCall" or the complete set of recursive functions.
                        initial_writing_variables = []
                        functions_writing_variables = []
                        for signature in list_of_results_reachable:
                            func = contract.get_function_from_signature(signature)
                            for each in check_writing_assembly(func):
                                functions_writing_variables.append(func.full_name)
                                initial_writing_variables.append(each)
                            for each in func.state_variables_written:
                                functions_writing_variables.append(func.full_name)
                                initial_writing_variables.append(str(each))

                        # When we know which variables are modified (if any), we want to know which other functions in the contract are writing to that variable.    
                        if initial_writing_variables:
                            initial_writing_variables = list(set(initial_writing_variables))
                            functions_writing_variables = list(set(functions_writing_variables)) 
                            # If we have other functions writing to the same variable which are not yet in list_of_functions, we add them.

                            # Unfortunately, for assembly variables we need to traverse again every function in the contract.
                            
                            for function in contract.functions:
                                temp_results = check_writing_assembly(function)
                                for temp_result in temp_results:
                                    if temp_result in initial_writing_variables and function.solidity_signature not in list_of_results_reachable:
                                        functions_writing_variables.append(function.full_name)
                            
                            for variable in initial_writing_variables:
                                temp_results = contract.get_functions_writing_to_variable(variable)
                                for temp_result in temp_results:
                                    if temp_result in initial_writing_variables:
                                        if temp_result in initial_writing_variables and function.solidity_signature not in list_of_results_reachable:
                                            functions_writing_variables.append(temp_result)

                        
                            # Now we need to find all the "FunctionCalls" that have _any_ of the functions in functions_writing_variables
                            for function in contract.functions:
                                results_internal = []
                                reachable_func_internal = {}
                                list_of_results_reachable_internal = []
                                get_reachable_functions_recursively(contract, function, results_internal, reachable_func_internal, list_of_results_reachable_internal)
                                list_of_results_reachable_internal = list(set(list_of_results_reachable_internal))

                                for result_reachable_internal in list_of_results_reachable_internal: 
                                    if result_reachable_internal in functions_writing_variables and non_inh_func.full_name not in reachable_func_internal.keys() and str(function.visibility) == "external" or str(function.visibility) == "public" and "constructor" not in function.full_name:

                                        # Maybe at this point we should print something to be manually validated, as we don't have as much certainty that this is an issue but it may be an interesting case.
                                
                                        # As we don't know at this point if the discovered function is also inherited nor if it is also overriden, and if we want to validate this outside the for loops we will need to save the information for reporting this, we need to come up with creative ways to validate if the discovered functions are in fact writing the underlying variable with fewer restrictions. 

                                        # For now, we will limit ourselves to verify if the discovered function is reading or writing the variables in the diff.

                                        #This will give us the first function in the function call
                                        function_call_alpha = list(reachable_func_internal.keys())[0]
                                        print(f"function_call_alpha {function_call_alpha}")
                                        alpha_function = contract.get_function_from_signature(function_call_alpha)

                                        local_result = []
                                        for var in diff_vars:
                                            if var not in alpha_function._vars_read_or_written:
                                                local_result.append(non_inh_func.full_name)
                                                local_result.append(var)
                                                local_result.append(function_call_alpha)
                                                detector_results.append(local_result)
    
    for detector_result in detector_results:
        print(f"In the overriden {detector_result[0]}, the {detector_result[1]} variable is read or written while in the {detector_result[2]}, the {detector_result[1]} does not exist")
    
    return detector_results

def find_function_difference(inh_function, non_inh_function):

    # Let's get the inherited function vars.
    inh_sol_vars = inh_function.solidity_variables_read
    inh_state_vars = inh_function._vars_read_or_written

    # Let's get the non inherited function vars.
    non_inh_sol_vars = non_inh_function.solidity_variables_read
    non_inh_state_vars = non_inh_function._vars_read_or_written

    if inh_sol_vars == non_inh_sol_vars and inh_state_vars == non_inh_state_vars:
        pass

    else:
        ### We will assume that differences will be always on the non_inherited variables.
        
        # We need to stringify the elements of the object or DeepDiff will not be able to parse the data inside the list.

        inh_sol_vars = [str(elem) for elem in inh_sol_vars]
        inh_state_vars = [str(elem) for elem in inh_state_vars]
        non_inh_sol_vars = [str(elem) for elem in non_inh_sol_vars]
        non_inh_state_vars = [str(elem) for elem in non_inh_state_vars]

        diff_sol = DeepDiff(inh_sol_vars, non_inh_sol_vars)
        diff_state = DeepDiff(inh_state_vars, non_inh_state_vars)

        return diff_sol, diff_state


def handle_results(diff, state, name):
    items = diff.items()
    every_instance = []
    for action, instances in items:

        for instance in instances.values():

            # We need to clean the results from the DeepDiff library 
            if "root" in instance:
                break

            if state:
                print(f"The overriden {name} function changes of {action} type, with state variable {instance}")
            else:
                print(f"The overriden {name} function changes of {action} type, with solidity variable {instance}")
            
            every_instance.append(instance)        

    return every_instance
