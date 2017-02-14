import random
import math
import operator

class DiceParser:
    # OP: [Precedence, Associativity]
    OPERATORS = {
        'd': {'pre':5, 'assoc':'NONE', 'func':lambda a,b:NotImplemented},
        '^': {'pre':4, 'assoc':'RIGHT', 'func':operator.pow},
        '*': {'pre':3, 'assoc':'LEFT', 'func':operator.mul},
        '/': {'pre':3, 'assoc':'LEFT', 'func':operator.truediv},
        '+': {'pre':2, 'assoc':'LEFT', 'func':operator.add},
        '-': {'pre':2, 'assoc':'LEFT', 'func':operator.sub},
        '>': {'pre':1, 'assoc':'NONE', 'func':lambda a,b:a>b},
        '<': {'pre':1, 'assoc':'NONE', 'func':lambda a,b:a<b},
        '==': {'pre':1, 'assoc':'NONE', 'func':lambda a,b:a==b},
        '!=': {'pre':1, 'assoc':'NONE', 'func':lambda a,b:a!=b},
        '>=': {'pre':1, 'assoc':'NONE', 'func':lambda a,b:a>=b},
        '<=': {'pre':1, 'assoc':'NONE', 'func':lambda a,b:a<=b}
    }

    # NAME: ARG_COUNT, FUNC
    FUNCTIONS = {
        'ceil': {'args':1, 'func':math.ceil},
        'floor': {'args':1, 'func':math.floor},
        'if': {'args':3, 'func':lambda a,b,c:b if a else c}
    }
    
    def __init__(self):
        self.index = 0
        self.roll = ''

    def evaluateInfix(self, roll):
        postfixtokens = self.InfixToPostfix(roll)
        stack = []
        rolls = []
        for t in postfixtokens:
            if t['type'] == 'int':
                stack.append(int(t['val']))
            elif t['type'] == 'func':
                func = DiceParser.FUNCTIONS[t['val']]
                val = func['func'](*stack[-func['args']:])
                for i in range(func['args']):
                    stack.pop(-1)
                stack.append(val)
            elif t['type'] == 'op':
                arg2 = stack.pop(-1)
                arg1 = stack.pop(-1)
                val = 0
                if t['val'] == 'd':
                    r = []
                    for i in range(arg1):
                        r.append(random.randint(1, arg2))
                    val = sum(r)
                    rolls.append('{0:d}d{1:d}: {2} = {3}'.format(
                        arg1, arg2, val, ', '.join(str(x) for x in r)))
                else:
                    val = DiceParser.OPERATORS[t['val']]['func'](arg1, arg2)
                stack.append(val)
        if len(stack) != 1:
            print(stack)
            raise ValueError('Roll was invalid, final stack size not 1')
        output = '\n'.join(rolls)
        if output:
            output += '\n'
        output += 'Total: {0}'.format(stack[0])
        return output

    
    def InfixToPostfix(self, roll):
        self.index = 0
        self.roll = roll

        output_stack = []
        stack = []
        function_arg_count_stack = []
        
        while self.index < len(self.roll):
            t = self.__getToken()
            if t['type'] == 'int':
                output_stack.append(t)
            elif t['type'] == 'func':
                if t['val'] in DiceParser.FUNCTIONS:
                    stack.append(t)
                    function_arg_count_stack.append(DiceParser.FUNCTIONS[t['val']]['args'])
                else:
                    raise ValueError('Unknown Function "{0}" at {1}'.format(t['val'], t['index']))
            elif t['type'] == 'argsep':
                if len(function_arg_count_stack) == 0:
                    raise ValueError('Extra argument at "{0}"'.format(t['index']))
                else:
                    function_arg_count_stack[-1] -= 1
                    while len(stack) > 0 and stack[-1]['val'] != '(':
                        output_stack.append(stack.pop(-1))
            elif t['type'] == 'paren':
                if t['val'] == '(':
                    stack.append(t)
                elif t['val'] == ')':
                    while len(stack) > 0 and stack[-1]['val'] != '(':
                        output_stack.append(stack.pop(-1))
                    stack.pop(-1)
                    if len(stack) > 0 and stack[-1]['type'] == 'func':
                        if function_arg_count_stack[-1] > 1:
                            raise ValueError('Not enough arguments for function "{0}" at {1}'
                                .format(stack[-1]['val'], stack[-1]['index']))
                        function_arg_count_stack.pop(-1)
                        output_stack.append(stack.pop(-1))
            elif t['type'] == 'op':
                if t['val'] in DiceParser.OPERATORS:
                    op = DiceParser.OPERATORS[t['val']]
                    while len(stack) > 0 and stack[-1]['type'] == 'op':
                        otherop = DiceParser.OPERATORS[stack[-1]['val']]
                        if op['assoc'] == 'NONE' and otherop['assoc'] == 'NONE' and \
                           op['pre'] == otherop['pre']:
                            raise ValueError('Operator "{0}" cannot be chained with {1} at {2}'
                                .format(t['val'], stack[-1]['val'], t['index']))
                        elif (op['assoc'] == 'LEFT' and op['pre'] <= otherop['pre']) or \
                           (op['assoc'] in ['RIGHT', 'NONE'] and op['pre'] < otherop['pre']):
                            output_stack.append(stack.pop(-1))
                        else:
                            break
                    stack.append(t)
                else:
                    raise ValueError('Unknown Operator "{0}" at {1}'.format(t['val'], t['index']))
            else:
                raise ValueError('Unknown Token Type "{0}" at {1}'.format(t['type'], t['index']))
        
        while len(stack) > 0:
            if stack[-1]['type'] == 'paren':
                raise ValueError('Unmatched Parentheses start at {0}'.format(stack[-1]['index']))
            else:
                output_stack.append(stack.pop(-1))

        return output_stack

    def __beforeEnd(self):
        return self.index + 1 < len(self.roll)

    def __skipWhitespace(self):
        while self.__beforeEnd() and self.roll[self.index].isspace():
            self.index += 1

    def __matchesName(self, names, index):
        return any(map(lambda n:self.roll.startswith(n, index), names))

    def __getToken(self):
        self.__skipWhitespace()

        startindex = self.index
        if self.roll[self.index].isdigit():
            while self.__beforeEnd() and self.roll[self.index+1].isdigit():
                self.index += 1
            self.index += 1
            out = {'index':startindex, 'type':'int','val':self.roll[startindex:self.index]}
        elif self.__matchesName(DiceParser.OPERATORS, startindex):
            self.index += 1
            out = {'index':startindex, 'type':'op','val':self.roll[startindex:self.index]}
        elif self.__matchesName(DiceParser.FUNCTIONS, startindex):
            while self.__beforeEnd() and self.roll[self.index+1].isalpha():
                self.index += 1
            self.index += 1
            out = {'index':startindex, 'type':'func','val':self.roll[startindex:self.index]}
        elif self.roll[self.index] == ',':
            self.index += 1
            out = {'index':startindex, 'type':'argsep', 'val':','}
        elif self.roll[self.index] in ['(', ')']:
            self.index += 1
            out = {'index':startindex, 'type':'paren', 'val': self.roll[startindex]}
        else:
            raise ValueError('Unknown Token at {0}'.format(startindex))
        return out

if __name__ == '__main__':
    DP = DiceParser()

    parseTests = {
        'Basic Die Roll': ['4d6', '4 6 d'],
        'Basic Arithmetic': ['1+2-3*4/2+1', '1 2 + 3 4 * 2 / - 1 +']
    }

    evaluateTests = {
        'Basic Arithmetic': ['1+2-3*4/2+1', 'Total: -2.0']
    }

    def runParseTests(tests):
        for test in tests:
            try:
                postfixTokens = DP.InfixToPostfix(tests[test][0])
                postfixForm = ' '.join(t['val'] for t in postfixTokens)
                if tests[test][1] == postfixForm:
                    print(test + ': Success')
                else:
                    print(test + ': Failed\nActual Result: ' + postfixForm)
            except Exception as err:
                print(test + ': Failed\nError: ' + err)

    def runEvaluateTests(tests):
        for test in tests:
            try:
                value = DP.evaluateInfix(tests[test][0])
                if tests[test][1] == value:
                    print(test + ': Success')
                else:
                    print(test + ': Failed\nActual Result: ' + value)
            except Exception as err:
                print(test + ': Failed\nError: ' + err)