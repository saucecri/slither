import collections
import re

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

def get_reachable_functions_recursively(contract, function, results, reachable_func, list_of_functions):
    """
    From a Slither function object and a function name, generates the complete set of recursive reachable functions.
    """ 

    # For each function in the contract
    for local_function in contract.functions:
        counter = 0
        last_match = 0
        # For each reachable function in the current function
        for reachable in local_function.reachable_from_functions:
            counter = counter + 1
            # Let's check if the current function we are analyzing is reachable 
            if reachable == function:

                # If it is reachable and not already saved, we save it in reachable_func[function.full_name]

                if function.full_name not in reachable_func:
                    last_match = counter
                    reachable_func[function.full_name] = [local_function.full_name]
                    list_of_functions.append(function.solidity_signature)
                    list_of_functions.append(local_function.solidity_signature)

                else:
                    # if it is reachable and we already have something saved there, we save it in reachable_func[local_function.full_name] as a nested dict
                    #print(f"SOYELELSE {reachable_func[function.full_name]}, {local_function.solidity_signature} ")
                    reachable_func[function.full_name].append(local_function.full_name)
                    list_of_functions.append(local_function.solidity_signature)


                results.append(reachable_func)

    list_of_functions = list(set(list_of_functions))

    return results, list_of_functions

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


def build_recursive_dict(reachable_func):
    """
        It generates a recursive nested dict from the result of the get_reachable_functions_recursively function.
    """
    print(f"type(reachable_func) {type(reachable_func)}")

    nested_dict_reachable = reachable_func.copy()
    counter = 0
    list_of_keys_to_delete = []
    for list_of_reachable in reachable_func.values():
                            
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