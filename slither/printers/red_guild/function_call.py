from slither.printers.red_guild.utils import get_reachable_functions_recursively, check_writing_assembly, build_json_from_reachable, get_recursive_calls, get_all_calls, set_ext_reachable_from_function
from slither.tools.possible_paths.possible_paths import find_target_paths
from slither.core.declarations import Function
from slither.core.declarations import Contract, Function, FunctionContract
from slither.slithir.operations import LowLevelCall, InternalCall, LibraryCall, HighLevelCall

class FunctionCall:

    def __init__(self, slither, contract,  alpha_function):
        assert alpha_function
        # Alpha function data
        self.alpha_function = alpha_function.full_name
        self.alpha_function_visibility = alpha_function.visibility

        # Results and recursive data structures 
        self.results = []
        self.reachable_func = {}
        self.list_of_functions = []
        self.list_of_ins_functions = []

        # Store alpha_function varfget_reachable_functions_recursivelyiables information
        self.written_variables = {self.alpha_function: [str(x) for x in alpha_function.state_variables_written  + alpha_function.all_state_variables_written()]}
        self.read_variables = {self.alpha_function:  [str(x) for x in alpha_function.state_variables_read + alpha_function.solidity_variables_read + alpha_function.all_state_variables_read()]}
        self.variables = { self.alpha_function:  [x for x in alpha_function.variables]}
        
        # Store recursive variable information
        self.all_conditional_state_variables_read = { self.alpha_function: [x for x in alpha_function.all_conditional_state_variables_read()]}
        self.all_conditional_solidity_variables_read = { self.alpha_function: [x for x in alpha_function.all_conditional_solidity_variables_read()] }
        self.all_state_variables_read = { self.alpha_function: [x for x in alpha_function.all_state_variables_read()]}
        self.all_state_variables_written = { self.alpha_function: [x for x in alpha_function.all_state_variables_written()]}

        # Store alpha_function recursive calls information
        self.all_high_level_calls = { self.alpha_function: [[contract,target] for (contract,target) in alpha_function.all_high_level_calls()]}
        self.all_low_level_calls = { self.alpha_function: [[contract,target] for (contract,target) in alpha_function.all_low_level_calls()]}
        self.all_library_calls = { self.alpha_function: [[contract,target] for (contract,target) in alpha_function.all_library_calls()]}
        self.all_internal_calls = { self.alpha_function: [[target] for (target) in alpha_function.all_internal_calls()]}
        self.all_solidity_calls = { self.alpha_function: [[target] for (target) in alpha_function.all_solidity_calls()]}
        self.external_calls_as_expressions = alpha_function.external_calls_as_expressions
        print(f"external_calls_as_exp {self.external_calls_as_expressions}")
        for call in self.all_high_level_calls:
            print(f"high_level_call_g {call}")
        for call in self.external_calls_as_expressions:
            print(f"call._called {call._called},call._arguments {call._arguments},call._type_call {call._type_call},type(call) {type(call)}")
            # We match interfaces
            if str(call._called)[0] == "I":
                call._called = str(call._called)[1:]
                print(f"stripped_called {call._called}")
                
        """
        self.results_2 = []
        self.reachable_func_2 = {}
        self.list_of_functions_2 = []
        self.reachable_func_str = {}
        self.list_of_functions_str = []
        self.list_of_keys = []

        print(f"alpha_function_2 {type(alpha_function)}")

        lll,pp = get_recursive_calls(alpha_function, self.results_2, self.reachable_func_2, self.list_of_functions_2, self.reachable_func_str, self.list_of_functions_str, self.list_of_keys)
        
        print(f"self.results_2 {self.results_2}, self.reachable_func_2 {self.reachable_func_2},self.list_of_functions_2 {self.list_of_functions_2}, lll {lll}. pp {pp}")
        for function in self.list_of_functions_2:
            aa, bb = get_recursive_calls(function, self.results_2, self.reachable_func_2, self.list_of_functions_2, self.reachable_func_str, self.list_of_functions_str, self.list_of_keys)
            print(f"aaaa {aa}, bbbbb {bb}")

        print(f"self.results_3 {self.results_2}, self.reachable_func_3 {self.reachable_func_2},self.list_of_functions_3 {self.list_of_functions_2}, reachable_func_3 {self.reachable_func_str}")

        #print(f"self.reachable_func_2 {self.reachable_func_2}, self.list_of_functions_2 {self.list_of_functions_2}, self.results_2 {self.results_2}")
        """
        # Store alpha_function calls information
        self.solidity_calls = { self.alpha_function: [x for x in alpha_function.solidity_calls]}
        self.high_level_calls = { self.alpha_function: [[contract,target] for (contract,target) in alpha_function.high_level_calls]}
        self.low_level_calls = { self.alpha_function: [[contract,target] for (contract,target) in alpha_function.low_level_calls]}
        self.library_calls =  { self.alpha_function: [[contract,target] for (contract,target) in alpha_function.library_calls]}
        self.internal_calls = { self.alpha_function: [[target] for (target) in alpha_function.internal_calls]}
        self.external_calls = { self.alpha_function: [[target] for (target) in alpha_function.solidity_calls]}


        # Store alpha_function additional data
        self.modifiers = { self.alpha_function: [str(x) for x in alpha_function.modifiers]}
        self.internal_calls_as_signatures = { self.alpha_function: [str(x) for x in alpha_function.internal_calls_as_signatures]}
        self.reading_in_require_or_assert = []
        self.list_of_function_objects = []
        self.parameters = { self.alpha_function: [x for x in alpha_function.parameters]}
        self.paths_target = find_target_paths(slither, [alpha_function])

        list_reading_in_require_or_assert = []
        list_reading_in_conditional_nodes = []
        
        for variable in alpha_function.variables:
            if  alpha_function.is_reading_in_require_or_assert(variable):
                list_reading_in_require_or_assert.append(variable)
            if alpha_function.is_reading_in_conditional_node(variable):
                list_reading_in_conditional_nodes.append(variable)
        
        self.is_reading_in_require_or_assert = {self.alpha_function: list_reading_in_require_or_assert}
        self.is_reading_in_conditional_node = {self.alpha_function: list_reading_in_conditional_nodes}
        
        # We clean the duplicates and store the clean data
        self.results_dict = build_json_from_reachable(self.reachable_func)
        print(f"self.results_dict_1 {self.results_dict}")
        #print(f"results_dict {self.results_dict}")
        get_reachable_functions_recursively(contract, alpha_function, self.results, self.reachable_func, self.list_of_functions, self.list_of_ins_functions)
        
        print(f"self.list_of_functions_1 {self.list_of_functions} self.reachable_func_1 {self.reachable_func}, self.results_1 {self.results}")
        
        # We start to look for data on the flow
        for function_name in self.list_of_functions:
            func = contract.get_function_from_signature(function_name)
            if not func:
                func = next((function for function in contract.functions if function.name == function_name.name), None)

            assert func

            func.get_call_as_ops()
            if func.call_as_ops:
                #print(f"(func.get_all_ops) {func.call_as_ops}")
                for op in func.call_as_ops:
                    if isinstance(op, LibraryCall) or isinstance(op, HighLevelCall) or isinstance(op, LowLevelCall):
                        print(f"op.destination {op.destination}")
                        if isinstance(op.destination, Contract):
                            cont = op.destination

                        elif str(op.destination.type)[0] == "I":
                            non_int_cont = str(op.destination.type).lstrip("I")
                            cont = next((contract for contract in slither.contracts if contract.name == non_int_cont), None)
                        else:
                            cont = next((contract for contract in slither.contracts if contract.name == op.destination.type), None)
                    elif isinstance(op,InternalCall):
                        cont = next((contract for contract in slither.contracts if contract.name == op.contract_name), None)
                    if cont is None:
                        print(f"cont is None_ops {op}, op.destination {op.destination.type}, {type(op.destination.type)}")
                        pass
                    _func = next((function for function in contract.functions if function.name == op.function.name), None)
                    print(f"call_as_ops_ {op.function}")
                    print(f"call_as_ops_ {_func}")
                    print(f"type(call_as_ops_) {type(_func)}")    
                    if _func:
                        set_ext_reachable_from_function(func , _func)
                    self.list_of_ins_functions.append(op.function)

            if func.call_as_str:
               for c,f in func.call_as_str:
                    cont = next((contract for contract in slither.contracts if contract.name == c), None)
                    if cont is None:
                        for contract in slither.contracts:
                            print(f"cont is None_str {c}, {contract.name}")
                        pass
                    _func = next((function for function in cont.functions if function.name == f), None)
                    assert cont, _func

                    print(f"call_as_str_")
                    print(f"type(call_as_str_) {type(_func)}")
                    set_ext_reachable_from_function(func, _func)
                    self.list_of_ins_functions.append(_func)
                    print(f"call_as_string {c}.{f}")
                    print(f"call_as_string_2 {type(cont)}.{type(func)}")
            else:
                print(f"not call_as_op")
            
            for r in self.list_of_ins_functions:
                print(f"self.list_of_ins_functions {r} for {func.contract_declarer}.{func.full_name}")

            get_reachable_functions_recursively(contract, func, self.results, self.reachable_func, self.list_of_functions, self.list_of_ins_functions)

            #print(f"reachable_func {self.reachable_func}")
            #print(f"FunctionCall::func {func}")
            #print(f"self.results {self.results}")
            
            self.written_variables[function_name] = [str(x) for x in func.state_variables_written  + func.all_state_variables_written()]
            self.read_variables[function_name] = [str(x) for x in func.state_variables_read + func.solidity_variables_read + func.all_state_variables_read()]
            self.variables[function_name] = [x for x in func.variables]
            
            self.parameters[function_name] = [x for x in func.parameters]
            #self.all_conditional_state_variables_read.append([str(x) for x in func.conditional_state_variable_read])
            
            #self.all_conditional_solidity_variables_read.append([str(x) for x in func.conditional_solidity_variable_read])
            

            self.all_high_level_calls[function_name] = [[contract,target] for (contract,target) in func.all_high_level_calls()]
            self.all_internal_calls[function_name] = [[target] for (target) in func.all_internal_calls()]
            self.all_library_calls[function_name] = [[contract,target] for (contract,target) in func.all_library_calls()]
            self.all_low_level_calls[function_name] = [[contract,target] for (contract,target) in func.all_library_calls()]
            
            self.high_level_calls[function_name] = [[contract,target] for (contract,target) in func.high_level_calls]
            self.library_calls[function_name] = [[contract,target] for (contract,target) in func.library_calls]
            self.low_level_calls[function_name] = [[contract,target] for (contract,target) in func.library_calls]
            self.internal_calls[function_name] = [[target] for (target) in func.internal_calls]

            self.internal_calls_as_signatures[function_name] = [str(x) for x in func.internal_calls_as_signatures]
            self.external_calls[function_name] = [str(x) for x in func.external_calls_as_expressions]

            #self.all_state_variables_read[function_name] = [str(x) for x in func.state_variables_read]
            #self.all_state_variables_written[function_name] = [str(x) for x in func.state_variables_written]
            
            #self.variable_written_in_assembly.append([str(x) for x in func.variables_written_in_assembly])

            self.modifiers[function_name] = [x for x in func.modifiers]
            
            #print(f"type(func) {type(func)}")
            list_of_read_req = []
            list_of_read_cond = []

            for variable in func.variables:
                if func.is_reading_in_require_or_assert(variable):
                    list_of_read_req.append(variable)
                if alpha_function.is_reading_in_conditional_node(variable):
                    list_of_read_cond.append(variable)
            
            self.is_reading_in_require_or_assert[function_name] = list_of_read_req
            self.is_reading_in_conditional_node[function_name] = list_of_read_cond

            # Here we should look for new paths ?
            #for path in self.paths_target:
                #print(f"path {path}")
            #    break

        # We don't need to print this as the correct version is after build_recursive_dict
        print(f"SECOND self.reachable_func {self.reachable_func}")
        
        self.results_dict = build_json_from_reachable(self.reachable_func)
        #self.results_dict_2 = build_json_from_reachable(self.reachable_func_str)
        #print(f"DAME_LA_POSTA {self.results_dict_2}")

        print(f"self.results_dict {self.results_dict}")
