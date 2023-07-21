"""
    Function module
"""
from typing import Dict, TYPE_CHECKING, List, Tuple, Optional

from slither.core.declarations.contract_level import ContractLevel
from slither.core.declarations import Function
from slither.utils.code_complexity import compute_cyclomatic_complexity


# pylint: disable=import-outside-toplevel,too-many-instance-attributes,too-many-statements,too-many-lines

if TYPE_CHECKING:
    from slither.core.declarations import Contract
    from slither.core.scope.scope import FileScope
    from slither.slithir.variables.state_variable import StateIRVariable
    from slither.core.compilation_unit import SlitherCompilationUnit


class FunctionContract(Function, ContractLevel):
    def __init__(self, compilation_unit: "SlitherCompilationUnit") -> None:
        super().__init__(compilation_unit)
        self._contract_declarer: Optional["Contract"] = None

    def set_contract_declarer(self, contract: "Contract") -> None:
        self._contract_declarer = contract

    @property
    def contract_declarer(self) -> "Contract":
        """
        Return the contract where this function was declared. Only functions have both a contract, and contract_declarer
        This is because we need to have separate representation of the function depending of the contract's context
        For example a function calling super.f() will generate different IR depending on the current contract's inheritance

        Returns:
            The contract where this function was declared
        """

        assert self._contract_declarer
        return self._contract_declarer

    @property
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        if self._canonical_name is None:
            name, parameters, _ = self.signature
            self._canonical_name = (
                ".".join([self.contract_declarer.name] + self._internal_scope + [name])
                + "("
                + ",".join(parameters)
                + ")"
            )
        return self._canonical_name

    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract_declarer == contract

    @property
    def file_scope(self) -> "FileScope":
        return self.contract.file_scope

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions
    ###################################################################################
    ###################################################################################

    @property
    def functions_shadowed(self) -> List["Function"]:
        """
            Return the list of functions shadowed
        Returns:
            list(core.Function)

        """
        candidates = [c.functions_declared for c in self.contract.inheritance]
        candidates = [candidate for sublist in candidates for candidate in sublist]
        return [f for f in candidates if f.full_name == self.full_name]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def get_summary(
        self,
    ) -> Tuple[str, str, str, List[str], List[str], List[str], List[str], List[str], int]:
        """
            Return the function summary
        Returns:
            (str, str, str, list(str), list(str), listr(str), list(str), list(str);
            contract_name, name, visibility, modifiers, vars read, vars written, internal_calls, external_calls_as_expressions
        """
        return (
            self.contract_declarer.name,
            self.full_name,
            self.visibility,
            [str(x) for x in self.modifiers],
            [str(x) for x in self.state_variables_read + self.solidity_variables_read],
            [str(x) for x in self.state_variables_written],
            [str(x) for x in self.internal_calls],
            [str(x) for x in self.external_calls_as_expressions],
            compute_cyclomatic_complexity(self),
        )

    def get_summary_2(
        self,
    ) -> Tuple[str, str, str, List[str], List[str], List[str], List[str], List[str], List[str]]:
        """
            Return the function summary
        Returns:
            (str, str, str, list(str), list(str), listr(str), list(str), list(str);
            contract_name, name, visibility, modifiers, vars read, vars written, internal_calls, external_calls_as_expressions
        """
        return (
            self.contract_declarer.name,
            self.full_name,
            self.visibility,
            [str(x) for x in self.modifiers],
            [str(x) for x in self.state_variables_read + self.solidity_variables_read],
            [str(x) for x in self.state_variables_written],
            [str(x) for x in self.internal_calls],
            [str(x) for x in self.external_calls_as_expressions],
            [str(x) for x in self.reachable_from_functions],
            [str(x) for x in self.all_library_calls()],
            [[contract,target] for (contract,target) in self.all_high_level_calls()]
        )

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIr and SSA
    ###################################################################################
    ###################################################################################

    def generate_slithir_ssa(
        self, all_ssa_state_variables_instances: Dict[str, "StateIRVariable"]
    ) -> None:
        from slither.slithir.utils.ssa import add_ssa_ir, transform_slithir_vars_to_ssa
        from slither.core.dominators.utils import (
            compute_dominance_frontier,
            compute_dominators,
        )

        compute_dominators(self.nodes)
        compute_dominance_frontier(self.nodes)
        transform_slithir_vars_to_ssa(self)
        if not self.contract.is_incorrectly_constructed:
            add_ssa_ir(self, all_ssa_state_variables_instances)

    def expressions_vars_written(self):
        
        return [str(x) for x in self.expressions_vars_written()]
    
    def written_variables(self):
        return [str(x) for x in filter( None, (self.variables_written, self.state_variables_written, self._expression_vars_written , self._state_vars_written))]

    def read_variables(self):
        return [str(x) for x in filter( None, (self.variables_read, self.state_variables_read, self.solidity_variables_read, self._state_vars_read , self._all_conditional_solidity_variables_read))]
    
    def all_low_level_calls_fc(self):
        return self.all_low_level_calls()

    def all_high_level_calls_fc(self):
        result = self.all_high_level_calls()
        print(f"high_level_fc {result}")
        return result
        
    def all_library_calls_fc(self):
        return self.all_library_calls()
        
    def all_internal_calls_fc(self):
        return self.all_internal_calls()
    
    def all_solidity_calls_fc(self):
        return self.all_solidity_calls()
"""
    def __hash__(self):
        return hash(str(self.contract_declarer) + self.name)

    def __eq__(self, other):
        if isinstance(other, FunctionContract):
            return (self.contract_declarer, self.name) == (other.contract_declarer, other.name)
        else:
            return str(self) == str(other)

    def __str__(self):
        return str(self.contract_declarer) +"."+ self.solidity_signature

 if function.full_name not in reachable_func:
                    last_match = counter
                    reachable_func[function.full_name] = [local_function.full_name]
                    if function.solidity_signature not in list_of_functions:
                        list_of_functions.append(function.solidity_signature)
                    if local_function.solidity_signature not in list_of_functions:
                        list_of_functions.append(local_function.solidity_signature)

                else:
                    # if it is reachable and we already have something saved there, we save it in reachable_func[local_function.full_name] as a nested dict

                    reachable_func[function.full_name].append(local_function.full_name)
                    
                    if function.solidity_signature not in list_of_functions:
                        list_of_functions.append(function.solidity_signature)
                    if local_function.solidity_signature not in list_of_functions:
                        list_of_functions.append(local_function.solidity_signature)


                results.append(reachable_func)

    list_of_functions = list(set(list_of_functions))

"""
            