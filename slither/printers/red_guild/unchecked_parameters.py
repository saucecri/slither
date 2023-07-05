import re
from slither.utils.colors import blue,green,yellow,red,magenta

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils import output


class UncheckedParameters(AbstractPrinter):
    WIKI = "https://github.com/crytic/slither/wiki/Printer-documentation#constructor-calls"
    ARGUMENT = "unchecked-parameters"
    HELP = "Print the unchecked-params"

    def output(self, _filename):
        res = ''
        for contract in self.contracts:
            result = unchecked_param_in_contract(contract)
            if type(result) != type(None):
                #print(f"RSULT: {result}")
                res = res.join(result)
        return self.generate_output(res)


def run_unchecked_parameters(file, contract=""):
    if contract != "":
        contract = file.get_contract_from_name(contract)
        unchecked_param_in_contract(contract)
    else:
        for contract in file.contracts:
            unchecked_param_in_contract(contract)
                # We first look for public/external callable functions
            
            
    # Or they are send unchecked as a parameter  of an internal/external function 

    # Then this is an interesting case

def unchecked_param_in_contract(contract):

    for function in contract.functions:
        require_results = []
        cond_results = []
        both_results = []
        if(function.visibility == "external" or function.visibility=="public"):
            # If function is not view or pure
            if not function.view and not function.pure:
            # If parameters and not being checked 

                for parameter in function.parameters:
                    
                    _require_results = check_parameter_not_in_require(function, parameter)
                    _cond_results = check_parameter_not_in_conditional(function, parameter)

                    if _require_results and _cond_results:
                        if _require_results == _cond_results:
                            for element in _require_results:
                                both_results.append(element)
                        else:
                            for element in _require_results:
                                both_results.append(element)
                            for element in _cond_results:
                                both_results.append(element)
                    else:
                        if _require_results:
                            for element in _require_results:
                                require_results.append(element)
                        elif _cond_results:
                            for element in _cond_results:
                                cond_results.append(element)
            
            # We remove duplicates
            #Sresults = list(dict.fromkeys(results))

            if require_results or both_results:
                print(blue(f"Results from {contract.name}.{function.canonical_name}"))
                if both_results:
                # We print results
                    print(red("When parameters not in `require` nor `if` condition : "))
                    print(*both_results, sep="\n")
                    return both_results
                elif require_results:
                    print(green("When parameters not in `require`: "))
                    print(*require_results, sep="\n")
                    return require_results
                else:
                    # So far this seems not interesting so we are not printing it
                    #print(yellow("When parameters not in conditional: "))
                    #print(*cond_results, sep="/n")
                    pass
                    


def interesting_expressions(expressions, parameter):
    regex = '(?:\()(.{1,})(?:\))'
    localResults = []
    for expression in expressions:
        # TODO: Handle case when require error message has str(parameter.name)
        # TODO: We don't want to catch when parameter used in events
                            
        # We check if they are using the parameter to write another variable
        match = f"= {parameter}"
        if match in str(expression):
            report = f"Unchecked param used to write variable: {str(expression)}"
            localResults.append(report)        
        
        # We check if parameter used in a call to other function
        second_match = re.search(regex, str(expression))
        if second_match:
            second_match = second_match.groups()[0]
            #print(f"second {second_match[0]}")
            if str(parameter) in second_match:
                # check_if_not_
                report = f"Unchecked param used as parameter in nested call: {str(expression)}"                
                localResults.append(report)
    return localResults

def check_parameter_not_in_require(function, parameter):
    if not function.is_reading_in_require_or_assert(parameter):
    #parameters.append(parameter)
    # And it's value is assigned to a variable
        _results = interesting_expressions(function.expressions, parameter)
        if _results:
            return _results
        else:
            return None

def check_parameter_not_in_conditional(function, parameter):
    if not function.is_reading_in_conditional_node(parameter):
    #parameters.append(parameter)
    # And it's value is assigned to a variable
        _results = interesting_expressions(function.expressions, parameter)
        if _results:
            return _results
        else:
            return None
        
"""
class UncheckedParameters(AbstractDetector):  # pylint: disable=too-few-public-methods


    ARGUMENT = "unchecked_parameters"  # slither will launch the detector with slither.py --mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "unchecked_param"

    WIKI_TITLE = "unchecked_param"
    WIKI_DESCRIPTION = "unchecked_param"
    WIKI_EXPLOIT_SCENARIO = "unchecked_param"
    WIKI_RECOMMENDATION = "unchecked_param"

    def _detect(self):

        
        return results



"""