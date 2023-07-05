from slither.slither import Slither
import sys
import re
from slither.utils.colors import blue, green, yellow, red, magenta
from slither.printers.abstract_printer import AbstractPrinter


class InternalFromExternal(AbstractPrinter):

    ARGUMENT = "internal-from-external"
    HELP = "Print the keccack256 signature of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#function-id"
    
    def output(self, _filename):
        txt = 'd'
        run(self)
        return self.generate_output(txt)


def get_int_functions(contract):
  """
  This function receives a Slither contract object as the input and saves the Internal and Private function in a dict where key = functionName,
  and value = visibility (for functions called without modifiers) or value = [visibility, modifier1, modifier2] (for functions called with modifiers)
  """
  dict = {}
  for func in contract.all_functions_called:
     if(func.visibility == "internal" or func.visibility=="private"):
       if(func.modifiers):
         modifiers = []
        # We are going to add the visibility as the first element of the list bc we need to save this value.
         modifiers.append(func.visibility)
         for modifier in func.modifiers:
           modifiers.append(modifier.name)
         dict[func.name] = modifiers
       else:
         dict[func.name] = func.visibility
  return dict 

def run(self):

  txt = ''
  pattern = '(\w*)\.(\w*)(\(.*\))'

  # Iterate over all contracts in the file
  for contract in self.contracts:
      diction = get_int_functions(contract)
    # Iterate over all the functions
      for function in contract.functions:
        if(function.visibility == "external" or function.visibility=="public"):
            #print('\tWritten {}'.format([v.name for v in function.state_variables_written]))

            # Iterate over the nodes of the function
              for node in function.nodes:

                # Iterate over every Intermediate Representation
                      for ir in node.irs:
                        text = '{}'.format(ir)
                        if("INTERNAL_CALL" in text):
                          regex = re.split(pattern, text)
                          internalContract = regex[1]
                          internalFunction = regex[2]
                          params = regex[3]
                          if (internalFunction in diction):
                            modifiers = function.modifiers
                            # get_int_functions adds a list as the 'value' of the dict if the function is called with modifiers. We check that to modify the print statement accordingly
                            if modifiers:
                                print(blue(contract.name +'.' + function.name) + ' calls ' +  green(internalContract + '.' + internalFunction) + yellow(' with modifiers: {}'.format([modifier.name for modifier in modifiers])))
                            else:
                             print(blue(contract.name +'.' + function.name) + ' calls ' +  green(internalContract + '.' + internalFunction))

#run("contracts/Test.sol")