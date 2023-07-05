from slither.printers.red_guild.utils import get_reachable_functions_recursively, check_writing_assembly, build_recursive_dict
from slither.tools.possible_paths.possible_paths import find_target_paths


class FunctionCall:

    def __init__(self, slither, contract,  alpha_function):
        self.alpha_function = alpha_function.full_name
        self.results = []
        self.reachable_func = {}
        self.list_of_functions = []
        self.written_variables = {}
        self.read_variables = {}
        self.variables = {}
        self.all_conditional_state_variables_read = []
        self.all_conditional_solidity_variables_read = []
        self.all_high_level_calls = []
        self.all_library_calls = []
        self.high_level_calls = {}
        self.library_calls = {}
        self.all_state_variables_read = []
        self.all_state_variables_written = []
        self.modifiers = []
        self.internal_calls = []
        self.external_calls = []
        self.all_internal_calls = []
        self.internal_calls_as_signatures = []
        self.external_calls_as_signatures = []
        self.library_calls_as_signatures = []
        self.high_level_calls_as_signatures = []
        self.all_external_calls = []
        self.reading_in_require_or_assert = []
        self.list_of_function_objects = []
        self.parameters = {}
        self.results_dict = build_recursive_dict(self.reachable_func)

        #print(f"results_dict {self.results_dict}")
        get_reachable_functions_recursively(contract, alpha_function, self.results, self.reachable_func, self.list_of_functions)

        
        for function_name in self.list_of_functions:
            func = contract.get_function_from_signature(function_name)
            #print(f"dir(func) {dir(func)}")

            if type(func) is type(None):
                print(f"function is None {function_name}")
                break

            get_reachable_functions_recursively(contract, func, self.results, self.reachable_func, self.list_of_functions)
            self.list_of_functions.append(func)

            #print(f"reachable_func {self.reachable_func}")
            #print(f"func {func}")
            #print(f"self.results {self.results}")
            
            self.written_variables[function_name] = [str(x) for x in func.state_variables_written  + func.all_state_variables_read()]


            self.read_variables[function_name] = [str(x) for x in func.state_variables_read + func.solidity_variables_read + func.all_state_variables_read() +  func.variables]
            
            
            self.variables[function_name] = [str(x) for x in func.variables]
            
            self.parameters[function_name] = [str(x) for x in func.parameters]
            #self.all_conditional_state_variables_read.append([str(x) for x in func.conditional_state_variable_read])
            
            #self.all_conditional_solidity_variables_read.append([str(x) for x in func.conditional_solidity_variable_read])
            

            self.all_high_level_calls.append([str(x) for x in func.all_high_level_calls()])
            
            self.high_level_calls[function_name] = [str(x) for x in func.high_level_calls]

            self.library_calls[function_name] = [str(x) for x in func.library_calls]

            self.all_library_calls.append([str(x) for x in func.all_library_calls()])


            self.all_state_variables_read.append([str(x) for x in func.state_variables_read])
            

            self.all_state_variables_written.append([str(x) for x in func.state_variables_written])
            
            #self.variable_written_in_assembly.append([str(x) for x in func.variables_written_in_assembly])

            self.modifiers.append([str(x) for x in func.modifiers])
            
            self.internal_calls.append([str(x) for x in func.internal_calls])

            #self.all_internal_calls.append([str(x) for x in func.all_internal_calls()])

            #self.all_external_calls.append([str(x) for x in func.all_external_calls()])

            self.internal_calls_as_signatures.append([str(x) for x in func.internal_calls_as_signatures])
            
            self.external_calls.append([str(x) for x in func.external_calls_as_expressions])

            for variable in func.variables:
                if func.is_reading_in_require_or_assert(variable):
                    self.reading_in_require_or_assert.append(variable)

            self.paths_target = find_target_paths(slither, [alpha_function])
            
            for path in self.paths_target:
                print(f"path {path}")
    
        self.results_dict = build_recursive_dict(self.reachable_func)
        print(f"self.results_dict {self.results_dict}")