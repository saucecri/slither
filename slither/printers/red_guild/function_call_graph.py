"""
    Module printing the call graph

    The call graph shows for each function,
    what are the contracts/functions called.
    The output is a dot file named filename.dot
"""
from collections import defaultdict
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable

from slither.printers.red_guild.utils import get_reachable_functions_recursively, build_recursive_dict
from slither.printers.red_guild.function_call import FunctionCall
from slither.tools.possible_paths.possible_paths import find_target_paths, resolve_functions


def _contract_subgraph(contract):
    return f"cluster_{contract.id}_{contract.name}"


# return unique id for contract function to use as node name
def _function_node(contract, function):
    return f"{contract.id}_{function.name}"


# return unique id for solidity function to use as node name
def _solidity_function_node(solidity_function):
    return f"{solidity_function.name}"


# return dot language string to add graph edge
def _edge(from_node, to_node):
    return f'"{from_node}" -> "{to_node}"'


# return dot language string to add graph node (with optional label)
def _node(node, label=None):
    return " ".join(
        (
            f'"{node}"',
            f'[label="{label}"]' if label is not None else "",
        )
    )


# pylint: disable=too-many-arguments
def _process_internal_call(
    contract,
    function,
    internal_call,
    contract_calls,
    solidity_functions,
    solidity_calls,
):
    if isinstance(internal_call, (Function)):
        contract_calls[contract].add(
            _edge(
                _function_node(contract, function),
                _function_node(contract, internal_call),
            )
        )
    elif isinstance(internal_call, (SolidityFunction)):
        solidity_functions.add(
            _node(_solidity_function_node(internal_call)),
        )
        solidity_calls.add(
            _edge(
                _function_node(contract, function),
                _solidity_function_node(internal_call),
            )
        )


def _render_external_calls(external_calls):
    return "\n".join(external_calls)


def _render_internal_calls(contract, contract_functions, contract_calls):
    lines = []

    lines.append(f"subgraph {_contract_subgraph(contract)} {{")
    lines.append(f'label = "{contract.name}"')

    lines.extend(contract_functions[contract])
    lines.extend(contract_calls[contract])

    lines.append("}")

    return "\n".join(lines)


def _render_solidity_calls(solidity_functions, solidity_calls):
    lines = []

    lines.append("subgraph cluster_solidity {")
    lines.append('label = "[Solidity]"')

    lines.extend(solidity_functions)
    lines.extend(solidity_calls)

    lines.append("}")

    return "\n".join(lines)


def _process_external_call(
    contract,
    function,
    external_call,
    contract_functions,
    external_calls,
    all_contracts,
):
    external_contract, external_function = external_call

    if not external_contract in all_contracts:
        return

    # add variable as node to respective contract
    if isinstance(external_function, (Variable)):
        contract_functions[external_contract].add(
            _node(
                _function_node(external_contract, external_function),
                external_function.name,
            )
        )

    external_calls.add(
        _edge(
            _function_node(contract, function),
            _function_node(external_contract, external_function),
        )
    )


# pylint: disable=too-many-arguments
def _process_function(
    contract,
    function,
    contract_functions,
    contract_calls,
    solidity_functions,
    solidity_calls,
    external_calls,
    all_contracts,
):
    contract_functions[contract].add(
        _node(_function_node(contract, function), function.name),
    )

    for internal_call in function.internal_calls:
        _process_internal_call(
            contract,
            function,
            internal_call,
            contract_calls,
            solidity_functions,
            solidity_calls,
        )
    for external_call in function.high_level_calls:
        _process_external_call(
            contract,
            function,
            external_call,
            contract_functions,
            external_calls,
            all_contracts,
        )


def _process_functions(functions):
    contract_functions = defaultdict(set)  # contract -> contract functions nodes
    contract_calls = defaultdict(set)  # contract -> contract calls edges

    solidity_functions = set()  # solidity function nodes
    solidity_calls = set()  # solidity calls edges
    external_calls = set()  # external calls edges

    all_contracts = set()

    for function in functions:
        all_contracts.add(function.contract_declarer)
    for function in functions:
        _process_function(
            function.contract_declarer,
            function,
            contract_functions,
            contract_calls,
            solidity_functions,
            solidity_calls,
            external_calls,
            all_contracts,
        )

    render_internal_calls = ""
    for contract in all_contracts:
        render_internal_calls += _render_internal_calls(
            contract, contract_functions, contract_calls
        )

    render_solidity_calls = _render_solidity_calls(solidity_functions, solidity_calls)

    render_external_calls = _render_external_calls(external_calls)
    
    return render_internal_calls + render_solidity_calls + render_external_calls

class ResultContract():

    def __init__(self, name='', visi='', read_vars=[], written_vars=[], internal_calls=[], external_calls=[], flow=[]):
        pass

class ResultFunction():

    def __init__(self, name=[], visi=[], read_vars=[], written_vars=[], internal_calls=[], external_calls=[], flow=[]):
        self.name = []
        self.visi = []
        self.read_vars = []
        self.written_vars = []
        self.internal_calls = []
        self.external_calls = []


class FunctionCallGraph(AbstractPrinter):
    ARGUMENT = "function-call-graph"
    HELP = "Export the call-graph of the contracts to a dot file"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#call-graph"

    def output(self, filename):
        """
        Output the graph in filename
        Args:
            filename(string)
        """
        res = []
        
        result_contract = ResultContract()
        result_function = ResultFunction()
        list_dicts = {}

        for contract in self.contracts:
            
            result_contract.name = contract.name

            if contract.name == "AccountingOracle":
                (_, _, _, func_summaries, _) = contract.get_summary_2()


                # primero analizamos todas las funciones y creamos los flows, luego los preguntamos y ya
                for (
                _c_name,
                f_name,
                visi,
                modifiers,
                read,
                write,
                internal_calls,
                external_calls,
                reachable,
                ) in func_summaries:
                    
                    list_dicts[f_name] = (visi, modifiers, read, write, internal_calls, external_calls)

                #func_sum_dict = dict(zip(f_name, (_c_name, f_name, visi, modifiers, read, write, internal_calls, external_calls)))

                # el key deberia ser function name y el value el func_summary
                
                if list_dicts:
                    for (
                    _c_name,
                    f_name,
                    visi,
                    modifiers,
                    read,
                    write,
                    internal_calls,
                    external_calls,
                    reachable,
                    ) in func_summaries:
                        print(f"_c_name {_c_name}, f_name {f_name}, reachable {reachable}, external_calls {external_calls}")
                        
                        internal_denylist = ['keccak256(', 'abi.encode(', 'revert']

                        #if f_name == "submitReportData(AccountingOracle.ReportData,uint256)":
                        if f_name:
                            # si las funciones que llaman son internas, entonces vamos a buscar todas las variables leidas y escritas. tambien necesitamos las funcionees internas y externas para seguir yendo hasta el final
                            print(f"self.contracts {self.contracts}")
                            func_call  = FunctionCall(self, contract,  contract.get_function_from_signature(f_name) )

                            function_call_alpha = func_call.alpha_function
                            
                            # Aca tengo que agregar todos los calls
                            for var in func_call.internal_calls_as_signatures:
                                #print(f"typevar {type(func_call.internal_calls_as_signatures)}, type {type(var)} , var {var}")
                                for sign in var:

                                    for deny in internal_denylist:
                                        if sign.startswith(deny):
                                            var.remove(sign)
                                
                                for sign in var:
                                    internal_function = contract.get_function_from_signature(sign)
                                    #print(f"type(internal_function) {type(internal_function)}")
                                    
                                    if internal_function is None:
                                        print(f"internal_function is None {sign}")
                                        break

                                    # Aca tengo que añadir todos los elementos
                                    func_call.read_variables[sign].append([str(x) for x in internal_function.read_variables()])
                                    func_call.written_variables[sign].append([str(x) for x in internal_function.written_variables()])
                                    func_call.high_level_calls[sign].append([str(x) for x in internal_function.high_level_calls])
                                    func_call.library_calls[sign].append([str(x) for x in internal_function.library_calls])
                                    func_call.parameters[sign].append([str(x) for x in internal_function.parameters])
                                    #func_call.
                                                                             
                                    
                            print(f"func_call.read_variables {func_call.read_variables}")
                            print(f"func_call.written_variables {func_call.written_variables}")
                            print(f"func_call.high_level_calls {func_call.high_level_calls}")
                            print(f"func_call.library_calls {func_call.library_calls}")

                            #print(f"PORQUENOLLEGAS {external_calls}")

                            for ext_var in func_call.external_calls:
                                
                                for ext_sign in ext_var:
                                    print(f"ext_var {ext_var}, ext_sign {ext_sign}")

                                    for ext_deny in internal_denylist:
                                        
                                        if ext_sign.startswith(ext_deny):
                                            #print(f"deny {ext_deny}, sign.startswith(deny {ext_sign.startswith(ext_deny)}")
                                            ext_var.remove(ext_sign)
                                            #print(f"ext_var {ext_var}")
                                
                                #print(f"VAR {ext_var}")

                                for ext_sign in ext_var:
                                    print(f"contract {contract.name},sign {ext_sign}, var {ext_var}")

                            # Aca agrego las demas funciones que escriben a las variables read y written.

                            print(f"func_call.variables {func_call.variables}")  
                        
                        print(f"REACHING {[str(x) for x in reachable]}")
#                            for read_variable in func_call.variables[sign]:
#                                print(f"read_variable {read_variable} func_call.variables[sign] {func_call.variables[sign]}")
#                                pass

                            

                        
                            #print(f"reachable_func {reachable_func} list_of_results_reachable {list_of_results_reachable}")
        return self.generate_output(res)
"""
                            for internal_call in internal_calls:
                                
                                if internal_call not in internal_denylist:
                                    result_function.name.append(internal_call)
                                    result_function.visi.append(visi)
                                    result_function.internal_calls.append(internal_call)
                                    result_function.read_vars.append(read)
                                    result_function.written_vars.append(write)
                                    result_function.external_calls.append(external_calls)
                                    (visi_1, modifiers_1, read_1, write_1, internal_calls_1, external_calls_1) =  list_dicts[internal_call]
                                    print(f"internal_calls_1 {internal_calls_1}, internal_call {internal_call}")
                                    while internal_calls_1:
                                        result_function.visi.append(visi_1)
                                        result_function.modifiers.append(modifiers_1)
                                        result_function.read_vars.append(read_1)
                                        result_function.written_vars.append(write_1)
                                        result_function.external_calls.append(external_calls_1)
                                        result_function.internal_calls.append(internal_calls_1)

                            # si las funciones que llaman son externas, entonces vamos a buscar todas las variables leidas y escritas. tambien necesitamos las funcionees internas y externas para seguir yendo hasta el final
                            for external_call in external_calls:

                                result_function.external_calls.append(external_call)
                                #print(f"func_sum_dict {func_sum_dict}")
                                 
"""
                            #print(f"_c_name  {_c_name}, f_name {f_name}, visi {visi}, modifiers {modifiers}, read {read}, write {write}, internal_calls {internal_calls}, external_calls {external_calls}")
                            #print(f"result_function {result_function.read_vars} result_function.written {result_function.written_vars}, internal_calls {result_function.internal_calls}, external_calls {result_function.external_calls}")
