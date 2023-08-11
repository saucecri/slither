from slither.core.declarations import FunctionContract, Function
import collections
import re
from slither.core.declarations import SolidityFunction

def get_public_functions_writting_var(contract, var):
    funcs_writing = contract.get_functions_writing_to_variable(var)

    reportable_funcs_writing = set(list(filter(lambda func: is_public(func), funcs_writing)))
    reportable_funcs_writing.update(get_public_callers(funcs_writing))

    return list(reportable_funcs_writing)

def get_public_callers(functions):
    public_callers = set()

    for func in functions:
        callers, queue = set(), collections.deque([func])

        while queue:
            func_to_check = queue.popleft()

            for neighbour in func_to_check.reachable_from_functions:
                if neighbour not in callers:
                    queue.append(neighbour)
                    callers.add(neighbour)

                    if is_public(neighbour):
                        public_callers.add(neighbour)

    return public_callers

def is_public(func): # TODO rename?
    return (not func.is_shadowed or (func.is_shadowed and func.is_constructor)) and \
           func.visibility in ['public', 'external']

def check_writing_assembly(function):
    """
    It checks if the Solidity function is writing a memory slot using assembly
    """
    results = []
    if function.contains_assembly:
        for var in function.variables_read:
            try:
                if var.is_constant and str(var.type) == "bytes32":
                    for expression in function.expressions:
                        if str("= " + var.name) in str(expression):
                            regex = "(\w*|\d*)" + " = " +  var.name
                            regeng = re.compile(regex)
                            matches = regeng.findall(str(expression))

                    for node in function.all_nodes():
                        if "INLINE ASM" in str(node):
                            for match in matches:
                                # This will only catch when the expression is sstore(result, var.name). Further work should be done to handle whitespaces in between
                                if "sstore(" + match in str(node.inline_asm):
                                    results.append(str(var.name))


            except Exception as err:
                    # var may not have the `is_constant` property, so we just don't handle this cases
                    if "is_constant" in str(err):
                        pass
                    else:
                        print(f"Error in check_writing_assembly: {err}")
    
    return results 


def build_json_from_reachable(reachable_func):
    """
        It generates a JSON from the result of the get_reachable_functions_recursively function.
    """
    #print(f"type(reachable_func) {type(reachable_func)}")

    nested_dict_reachable = reachable_func.copy()
    counter = 0
    list_of_keys_to_delete = []
    for list_of_reachable in reachable_func.values():
        
        try:
            dict_key = list(reachable_func)[counter]
        
            for element in list_of_reachable:

                if element in reachable_func.keys():
                    
                    # This handles the case when a function call the same function with `super`
                    if element == dict_key:
                        break

                    local_dict = {element: nested_dict_reachable[element]}

                    index = list_of_reachable.index(element)
                    nested_dict_reachable[dict_key][index] = local_dict
                    list_of_keys_to_delete.append(element)
                    counter = counter + 1    

            list_of_keys_to_delete = list(dict.fromkeys(list_of_keys_to_delete))
                    
            for elem in list_of_keys_to_delete:
                del nested_dict_reachable[elem]
            print(f"nested_dict_reachable {nested_dict_reachable}")
            return nested_dict_reachable 
        
        except IndexError:
            print(f"err_nested_dict_reachable {nested_dict_reachable}, reachable_func")
            #print(f"{reachable_func}[counter] does not exist")
            return nested_dict_reachable



def build_recursive_dict(reachable_func):
    """
        It generates a recursive nested dict from the result of the get_reachable_functions_recursively function.
    """
    #print(f"type(reachable_func) {type(reachable_func)}")

    nested_dict_reachable = reachable_func.copy()
    counter = 0
    list_of_keys_to_delete = []
    for list_of_reachable in reachable_func.values():
        
        try:
            dict_key = list(reachable_func)[counter]
        
            for element in list_of_reachable:
                                
                if element in reachable_func.keys():
                    
                    # This handles the case when a function call the same function with `super`
                    if element == dict_key:
                        break

                    local_dict = {element: nested_dict_reachable[element]}
                    index = list_of_reachable.index(element)
                    nested_dict_reachable[dict_key][index] = local_dict
                    list_of_keys_to_delete.append(element)
                    counter = counter + 1    

            list_of_keys_to_delete = list(dict.fromkeys(list_of_keys_to_delete))
                    
            for elem in list_of_keys_to_delete:
                del nested_dict_reachable[elem]
            
            return nested_dict_reachable 
        
        except IndexError:
            #print(f"{reachable_func}[counter] does not exist")
            return nested_dict_reachable            

"""
def get_call_functions_recursively(list_of_function_contract):

    #From a Slither function contract object, generates the complete set of recursive reachable calls (internal,library,highlevel,lowlevel, solidity).

    #nested_dict_reachable = reachable_func.copy()
    counter = 0
    results = []
    list_of_keys_to_delete = []
    
    for function_contract in list_of_function_contract:

    # For each call in list_of_function_contract (either internal, library, high/low level, solidity call) we just instantiate the function, and we get all of its data via all_high_level_calls(), all_low_level_calls(), all_internal_calls(), all_solidity_calls(), all_library_calls() 
        #low_level, high_level, internal, library = function_contract.get_all_calls()
        #for call in low_level:
        #    results.append((call, LowLevelCallType))
        #for call in high_level:
        #    results.append((call, HighLevelCallType))
        #for call in internal:
        #    results.append((call, InternalCallType))
        #for call in library:
        #    results.append((call, LibraryCallType))

        print(f"target_2 {results}")
    #print(f"call_functions {results}")
        return 
    # If it is reachable and not already saved, we save it in reachable_func[function.full_name]
"""


def get_all_calls(alpha_function):
    """
        Return the function summary
    Returns:
        (str, str, str, list(str), list(str), listr(str), list(str), list(str);
        contract_name, name, visibility, modifiers, vars read, vars written, internal_calls, z
    """
    if isinstance(alpha_function,Function):
        result = [[target] for (target) in alpha_function.all_high_level_calls() if type(target) == FunctionContract]
        print(f"all_high_level_calls_1 {result}")
        return [
            [[target] for (target) in alpha_function.all_low_level_calls() if type(target) == FunctionContract],
            [[target] for (target) in alpha_function.all_high_level_calls() if type(target) == FunctionContract],
            [[target] for (target) in alpha_function.all_internal_calls() if type(target) == FunctionContract],
            [[target] for (target) in alpha_function.all_library_calls() if type(target) == FunctionContract]
            ]
    if isinstance(alpha_function,FunctionContract):
        result = [[target] for (target) in alpha_function.all_high_level_calls_fc() if type(target) == FunctionContract]
        print(f"")
        return [
            [[target] for (target) in alpha_function.all_low_level_calls_fc() if type(target) == FunctionContract],
            [[target] for (target) in alpha_function.all_high_level_calls_fc() if type(target) == FunctionContract],
            [[target] for (target) in alpha_function.all_internal_calls_fc],
            [[target] for (target) in alpha_function.all_library_calls_fc() if type(target) == FunctionContract]
        ]

def get_reachable_functions_recursively(contract, function, results, reachable_func, list_of_functions, list_of_ins_functions):
    """
    From a Slither function object and a function name, generates the complete set of recursive reachable functions.
    """ 
    print(f"get_reachable_functions_recursively called contract {contract.name}, function {function.name}, results {results}, reachable_func {reachable_func}, list_of_functions {list_of_functions}, list_of_ins_functions {list_of_ins_functions}")
    # For each function in the contract and already instantiated functions
    for local_function in contract.functions +  list_of_ins_functions:
        counter = 0
        last_match = 0
        # For each reachable function in the current function
        # As SolidityCalls don't have reachable_from_functions we should handle this case
        if isinstance(local_function,SolidityFunction):
            continue
        for reachable in local_function.reachable_from_functions:
            print(f"reachable_in_local_function {reachable.contract_declarer}.{reachable.full_name}, local_function {local_function.contract_declarer}.{local_function.full_name}")
            reachable_cf = f"{reachable.contract_declarer}.{reachable.full_name}"
            local_function_cf = f"{local_function.contract_declarer}.{local_function.full_name}"
            function_cf = f"{function.contract_declarer}.{function.full_name}"
            counter = counter + 1
            # Let's check if the current function we are analyzing is reachable 
            if str(reachable.contract_declarer) != "AccountingOracle":
                print(f"when not AccountingOracle: {function.contract_declarer}.{function.full_name}, reachable {reachable.contract_declarer}.{reachable.full_name}")
            #if reachable == function:
            if reachable_cf == function_cf:
                print(f"reachable by function {reachable.full_name}")

                # If it is reachable and not already saved, we save it in reachable_func[function.full_name]

                #if function.full_name not in reachable_func:
                if function_cf not in reachable_func.keys():
                    #reachable_func[function.full_name] = [local_function.full_name]
                    reachable_func[function_cf] = [local_function_cf]
                    if function.solidity_signature not in list_of_functions:
                        list_of_functions.append(function.solidity_signature)

                    if local_function.solidity_signature not in list_of_functions:
                        list_of_functions.append(local_function.solidity_signature)
                    
                
                else:
                    # if it is reachable and we already have something saved there, we save it in reachable_func[local_function.full_name] as a nested dict

                    #reachable_func[function.full_name].append(local_function.full_name)
                    reachable_func[function_cf].append(local_function_cf)
                    if function.solidity_signature not in list_of_functions:
                        list_of_functions.append(function.solidity_signature)
                    if local_function.solidity_signature not in list_of_functions:
                        list_of_functions.append(local_function.solidity_signature)
                results.append(reachable_func)
            
                if function.solidity_signature not in list_of_functions:
                    list_of_functions.append(function.solidity_signature)

                if local_function.solidity_signature not in list_of_functions:
                    list_of_functions.append(local_function.solidity_signature)                
    print(f"utils reachable_func {reachable_func}")
    list_of_functions = list(set(list_of_functions))

    return results, list_of_functions


def get_recursive_calls(alpha_function, results, reachable_func, list_of_functions, reachable_func_str, list_of_functions_str, list_of_str_keys):

    calls = get_all_calls(alpha_function)
    print(f"calls_GG {calls}")
    for sublist in calls:
        
        for call in sublist:
            for fc in call:
                alpha_name = f"{alpha_function.contract}.{alpha_function.solidity_signature}"
                local_function = f"{fc.contract_declarer}.{fc.solidity_signature}"
                print(f"REACHING_FUNC:alpha_name {alpha_name} type(fc) {local_function}, fc {fc}")
            # If it is in reachable_func_str and not already saved, we save it in reachable_func[function.contract + . + solidity_signature]
                if str(alpha_name) not in list_of_str_keys:
                    reachable_func[alpha_function] = [fc]
                    reachable_func_str[alpha_name] = [local_function]
                    list_of_str_keys.append(alpha_name)
                    
                    if str(alpha_name) not in list_of_functions_str:
                        list_of_functions.append(fc)
                        list_of_functions_str.append(local_function)
                    
                    if local_function not in list_of_functions_str:
                            list_of_functions.append(fc)
                            list_of_functions_str.append(local_function)
                else:
                    # if it is reachable and we already have something saved there, we save it in reachable_func[local_function.full_name] as a nested dict
                    print(f"reachable_func_u {reachable_func}, local_function_u {local_function}, alpha_function_u {alpha_function},list_of_functions_u  {list_of_functions}, reachable_func_str_u {reachable_func_str}, list_of_functions_str_u {list_of_functions_str}, alpha_name {alpha_name}")

                    if str(alpha_name) not in list_of_str_keys:
                        print(f"alpha_name {alpha_name}, list_of_str_keys {list_of_str_keys}, reachable_func.keys() {[x for x in reachable_func.keys()]}")
                    
                    reachable_func[alpha_function].append(fc)
                    reachable_func_str[alpha_name].append(local_function)

                    if alpha_name not in list_of_functions_str:
                        list_of_functions.append(alpha_function)
                        list_of_functions_str.append(alpha_name)

                    if local_function not in list_of_functions_str:
                            list_of_functions.append(fc)
                            list_of_functions_str.append(local_function)
            
            print(f"REACHABLEE {reachable_func_str}")
            results.append(reachable_func_str)
            
            list_of_functions.append(fc)
            list_of_functions_str.append(local_function)
            list_of_functions = list(set(list_of_functions))
            list_of_functions_str = list(set(list_of_functions_str))


    return results, reachable_func_str

#def set_ext_str_reachable_from_function(function):
    
def set_ext_reachable_from_function(origin_function, end_function):
    print(f"calling_set_ext {origin_function.name}, {end_function.name}")
    print(f"end_funtion {end_function.nodes} {end_function.all_internal_calls()} {end_function.all_high_level_calls()} {end_function.all_low_level_calls()} {end_function.external_calls_as_expressions} {end_function.all_library_calls()}")
    for node in end_function.nodes:
        print(f"node_in_set_ext {node}")
        for expr in node._expression_calls:
            print(f"expr_in_set_ext: {expr}")
            if isinstance(expr.called, str):
                print(f"is it str?")
                continue
            for ir in node.slithir_call_ops_generation(expr):
                print(f"ir_in_ops {str(ir)}, {origin_function.contract_declarer}.{origin_function.full_name}, end_ {end_function.contract_declarer}.{end_function.full_name}")
                origin_function.add_reachable_from_node(node, ir)
                for f in origin_function.reachable_from_functions:
                    print(f"is_in ? {f.contract_declarer}.{f.full_name}")