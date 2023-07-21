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

from slither.printers.red_guild.utils import get_reachable_functions_recursively, build_json_from_reachable
from slither.printers.red_guild.function_call import FunctionCall
from slither.core.declarations import Function, FunctionContract, Contract
from slither.tools.possible_paths.possible_paths import find_target_paths, resolve_functions

from pyvis.network import Network
import json 
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

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
        txt = ''
        list_dicts = {}
        results = []

        nt = Network('1920px', '50%', select_menu=True, filter_menu=True)

        for contract in self.contracts:
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
                all_library_calls,
                all_high_calls
                ) in func_summaries:
                    #print(f"GGALL_LIBRARY_CALLS {all_library_calls}")
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
                    all_library_calls,
                    all_high_calls
                    ) in func_summaries:
                        print(f"_c_name {_c_name}, f_name {f_name}, reachable {reachable}, external_calls {external_calls}")
                        
                        internal_denylist = ['keccak256(', 'abi.encode(', 'revert']

                        if f_name:
                            # si las funciones que llaman son internas, entonces vamos a buscar todas las variables leidas y escritas. tambien necesitamos las funciones internas y externas para seguir yendo hasta el final
                            #print(f"f_name {f_name}, {type(f_name)}")
                            
                            alpha_function = contract.get_function_from_signature(f_name)
                            if not alpha_function:
                                alpha_function = next((function for function in contract.functions if function.name == f_name.split("(")[0]), None)
                            #print(f"alpha_function {alpha_function}")
                            func_call  = FunctionCall(self, contract, alpha_function)
                            
                            assert func_call

                            function_call_alpha = func_call.alpha_function
                            
                            # Aca tengo que agregar todos los calls
                            for var in func_call.internal_calls_as_signatures.values():
                                #print(f"typevar {type(func_call.internal_calls_as_signatures)}, type {type(var)} , var {var}, func_call {func_call}")
                                

                                for sign in var:
                                    # We remove denylist
                                    for deny in internal_denylist:
                                        if sign.startswith(deny):
                                            var.remove(sign)
                                
                                for sign in var:
                                    internal_function = contract.get_function_from_signature(sign)
                                    #print(f"type(internal_function) {type(internal_function)}, sign {sign}")
                                    if not internal_function:
                                        internal_function = next((function for function in contract.functions if function.name == sign.split("(")[0]), None)
                                    if internal_function is None:
                                        #print(f"internal_function is None {sign}")
                                        break

                                    # Aca tengo que añadir todos los elementos

                                    func_call.read_variables[sign] = [x for x in internal_function.read_variables()]
                                    func_call.written_variables[sign] = [x for x in internal_function.written_variables()]
                                    #func_call.high_level_calls[sign] = [str(x) for x in internal_function.high_level_calls]
                                    #func_call.library_calls[sign] = [str(x) for x in internal_function.library_calls]
                                    func_call.parameters[sign] = [x for x in internal_function.parameters]


                            #for hl_call in func_call.high_level_calls:
                                
                            #print(f"func_call.high_level_calls {func_call.high_level_calls}")
                            #for lib_call in func_call.library_calls:

                                #print(f"lib_call {lib_call}")

                            #print(f"func_call.library_calls {func_call.library_calls}")



                                #print(f"VAR {ext_var}")

                                #for ext_sign in ext_var:
                                    # We add external calls dats
                                    #break
                                    #rint(f"EXTERNAL_CALL contract {contract.name},sign {ext_sign}")
                                    # [] TODO Slither esta tomando las llamadas a la libreria Unstructured Storage como un external call asique tenemos que limpiar ese falso positivo.
                                    #self.contracts


                            # Aca agrego las demas funciones que escriben a las variables read y written.

                            #print(f"func_call.variables {func_call.variables}")  

                        #print(f"REACHING {[str(x) for x in reachable]}")
                            # now we add func_call to the results list
                            assert func_call
                            results.append(func_call)
        G = nx.MultiDiGraph()

        # We print results
        for result in results:
            ## No se porque sin este check estoy recibiendo unos result None 
            print(f"result.alpha_function {result.alpha_function}")

            print(f"result.library_calls {result.library_calls}")
            list_of_all_calls_contract = []
            list_of_all_function_contract = []
            list_of_all_function = []
            
            for key in result.all_low_level_calls.keys():
                for value in result.all_low_level_calls[key]:
                    for v in value:
                        if type(v) == Contract:
                            list_of_all_calls_contract.append(v.name)
                        if type(v) == FunctionContract:
                            list_of_all_function_contract.append(v)
                        if type(v) == Function:
                            list_of_all_function.append(v.name)
            
            for key in result.all_high_level_calls.keys():
                for value in result.all_high_level_calls[key]:
                    for v in value:
                        if type(v) == Contract:
                            list_of_all_calls_contract.append(v.name)
                        if type(v) == FunctionContract:
                            list_of_all_function_contract.append(v)
                        if type(v) == Function:
                            list_of_all_function.append(v.name)   

            for key in result.all_library_calls.keys():
                for value in result.all_library_calls[key]:
                    for v in value:
                        if type(v) == Contract:
                            list_of_all_calls_contract.append(v.name)
                        if type(v) == FunctionContract:
                            list_of_all_function_contract.append(v)
                        if type(v) == Function:
                            list_of_all_function.append(v.name) 

            for key in result.all_internal_calls.keys():
                for value in result.all_internal_calls[key]:
                    for v in value:
                        if type(v) == Contract:
                            list_of_all_calls_contract.append(v.name)
                        if type(v) == FunctionContract:
                            list_of_all_function_contract.append(v)
                        if type(v) == Function:
                            list_of_all_function.append(v.name) 

            for key in result.all_solidity_calls.keys():
                for value in result.all_solidity_calls[key]:
                    for v in value:
                        if type(v) == Contract:
                            list_of_all_calls_contract.append(v.name)
                        if type(v) == FunctionContract:
                            list_of_all_function_contract.append(v)
                        if type(v) == Function:
                            list_of_all_function.append(v.name) 

            print(f"list_of_library_contracts {set(list_of_all_calls_contract)}, list_of_library_function_contract {list_of_all_function_contract},list_of_library_function {set(list_of_all_function)}")

            
            #print(f"result.written_variables {result.written_variables}")
            #print(f"result.read_variables {result.read_variables}")
            list_of_read_vars = []
            list_of_written_vars = []
            list_of_cond_sol_vars = []
            list_of_cond_state_vars = []
            list_of_vars = []

            #print(f"result.all_state_variables_read {result.all_state_variables_read}")
            for key in result.all_state_variables_read.keys():
                for value in result.all_state_variables_read[key]:
                    list_of_read_vars.append(value.name)

            for key in result.all_state_variables_written.keys():
                for value in result.all_state_variables_written[key]:
                    list_of_written_vars.append(value.name)
                        
            for key in result.all_conditional_solidity_variables_read.keys():
                for value in result.all_conditional_solidity_variables_read[key]:
                    list_of_cond_sol_vars.append(value.name)

            for key in result.all_conditional_state_variables_read.keys():
                for value in result.all_conditional_state_variables_read[key]:
                    list_of_cond_state_vars.append(value.name)
            
            for key in result.variables.keys():
                for value in result.variables[key]:
                    if type(value) is None:
                        continue
                    list_of_vars.append(f"{value.name}.{value.get_type}")

            print(f"all_state_variables_written:{set(list_of_written_vars)}")            
            print(f"all_conditional_solidity_variables_read:{set(list_of_cond_sol_vars)}")            
            print(f"all_conditional_state_variables_read:{set(list_of_cond_state_vars)}")
            print(f"all_state_variables_read:{set(list_of_read_vars)}")
            print(f"all_variables:{set(list_of_vars)}")

            #print(f"result.paths")
            #for val in result.paths_target:
            #    for v in val:
            #        print(f"v.contract_declarer {v.contract_declarer}, v.full_name {v}")
            
            list_of_modifiers = []
            list_of_parameters = []
            list_of_reading_in_require = []
            list_of_reading_in_cond = []
            print(f"result.parameters {result.parameters}")
            print(f"result.is_reading_in_conditional_node {result.is_reading_in_conditional_node}")
            print(f"result.is_reading_in_require_or_assert {result.is_reading_in_require_or_assert}")
            
            for key in result.modifiers.keys():
                for value in result.modifiers[key]:
                    list_of_modifiers.append(value)

            for key in result.parameters.keys():
                for value in result.parameters[key]:
                    list_of_parameters.append(value.name)
            
            for key in result.is_reading_in_require_or_assert.keys():
                for value in result.is_reading_in_require_or_assert[key]:
                    list_of_reading_in_require.append(value.name)

            for key in result.is_reading_in_require_or_assert.keys():
                for value in result.is_reading_in_require_or_assert[key]:
                    list_of_reading_in_require.append(value.name)

            for key in result.is_reading_in_require_or_assert.keys():
                for value in result.is_reading_in_conditional_node[key]:
                    list_of_reading_in_require.append(value.name)

            print(f"list_of_modifiers {set(list_of_modifiers)}")
            print(f"list_of_parameters {set(list_of_parameters)}")
            print(f"list_of_reading_in_require {set(list_of_reading_in_require)}")
            print(f"list_of_reading_in_require {set(list_of_reading_in_require)}")
            print(f"list_of_reading_in_cond {set(list_of_reading_in_cond)}")
            
            if result.alpha_function_visibility == 'public' or result.alpha_function_visibility == 'external':

                if not result.results_dict:
                    continue
            
                j = json.loads(str(result.results_dict).replace("\'", "\""))
                G = add_multidigraph_function_data(j, G)
                print(f"result.results_dict: {result.results_dict}")
            
        
        #print(f"G: {G}")
        num_layers = max(nx.get_node_attributes(G, 'layer').values()) + 1
        layer_pos = {layer: (layer * 2, 0) for layer in range(num_layers)}
        pos = nx.multipartite_layout(G, subset_key="layer", align="horizontal")
        #pos = nx.multipartite_layout(G, subset_key="layer", align="horizontal")
        nx.draw(G, pos, node_color='lightblue', node_size=800, alpha=0.8, with_labels=False)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrowsize=10, arrowstyle='->')
        nx.draw_networkx_labels(G, pos, font_size=10, font_color='black')

        
        nt.from_nx(G)
        #nt.toggle_physics(False)
        nt.show_buttons(True)
        nt.set_options("""
const options = {
  "configure": {
    "enabled": true
  },
  "nodes": {
    "borderWidth": null,
    "borderWidthSelected": null,
    "opacity": null,
    "size": null
  },
  "edges": {
    "color": {
      "inherit": true
    },
    "selfReferenceSize": null,
    "selfReference": {
      "angle": 0.7853981633974483
    },
    "smooth": false
  },
  "layout": {
    "hierarchical": {
      "enabled": true,
      "levelSeparation": 240,
      "nodeSpacing": 245,
      "treeSpacing": 245,
      "direction": "LR",
      "sortMethod": "directed",
      "shakeTowards": "roots"
    }
  },
  "interaction": {
    "hover": true,
    "keyboard": {
      "enabled": true
    },
    "multiselect": true,
    "navigationButtons": true
  },
  "manipulation": {
    "enabled": true
  },
  "physics": {
    "hierarchicalRepulsion": {
      "centralGravity": 0,
      "avoidOverlap": null
    },
    "minVelocity": 0.75,
    "solver": "hierarchicalRepulsion"
  }
}""")
        nt.show("function_call.html")        

        return self.generate_output(res)

def add_multidigraph_function_data(data, G):
    for key, value in data.items():
        print(f"layer0 {key}")
        G.add_node(key, layer=0)  # Assigning layer attribute to nodes
        if isinstance(value, list):
            for element in value:
                if isinstance(element, dict):
                    for sub_key, sub_value in element.items():
                        #print(f"layer1_1 {sub_key}")
                        G.add_node(sub_key, layer=1)  # Assigning layer attribute to nodes
                        G.add_edge(key, sub_key)
                        if isinstance(sub_value, list):
                            for sub_element in sub_value:
                                #print(f"layer2_1 {sub_element}")
                                G.add_node(sub_element, layer=2)  # Assigning layer attribute to nodes
                                G.add_edge(sub_key, sub_element)
                        else:
                            #print(f"layer2_1 {sub_value}")
                            G.add_node(sub_value, layer=2)  # Assigning layer attribute to nodes
                            G.add_edge(sub_key, sub_value)
                else:
                    #print(f"layer1_2 {element}")
                    G.add_node(element, layer=1)  # Assigning layer attribute to nodes
                    G.add_edge(key, element)

    return G
