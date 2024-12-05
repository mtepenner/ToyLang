# Matthew Penner
#

# CS358 Fall'24 Assignment 4 (Part B)
#
# ToyLang - an imperative language with lambda functions
#
#   prog -> stmt
#
#   stmt -> "var" ID "=" expr
#         | "print" "(" expr ")"
#         | "{" stmt (";" stmt)* "}" 
#
#   expr -> "lambda" ID ":" expr
#         | expr "(" expr ")"
#         | aexpr 
#
#   aexpr -> aexpr "+" term
#          | aexpr "-" term
#          | term         
#
#   term -> term "*" atom
#         | term "/" atom
#         | atom
#
#   atom: "(" expr ")"
#         | ID
#         | NUM
#
from lark import Lark, v_args
from lark.visitors import Interpreter
import copy
debug = False

grammar = """
  ?start: stmt

  stmt: "var" ID "=" expr         -> decl
       | "def" ID "(" ID ")" "=" body  -> funcdecl
       | ID "=" expr               -> assign
       | "if" "(" expr ")" stmt ["else" stmt] -> ifstmt
       | "while" "(" expr ")" stmt -> whstmt
       | "print" "(" expr ")"      -> prstmt
       | "{" stmt (";" stmt)* "}"  -> block      

  ?expr: "lambda" ID ":" expr      -> func
       | expr "(" expr ")"         -> call
       | aexpr 

  ?aexpr: aexpr "+" term  -> add
       |  aexpr "-" term  -> sub
       |  term         

  ?term: term "*" atom  -> mul
       | term "/" atom  -> div
       | atom

  ?atom: "(" expr ")"
       | ID             -> var
       | NUM            -> num

  body: "{" (stmt ";")* "return" expr "}"

  %import common.WORD   -> ID
  %import common.INT    -> NUM
  %import common.WS
  %ignore WS
"""

parser = Lark(grammar, parser='lalr')

# Variable environment
#
class Env(dict):
    def __init__(self):
        super().__init__()
        self.prev = []  
    def openScope(self):
        self.prev.append(self.copy())
        self.clear()
    def closeScope(self):
        if not self.prev:
            raise Exception("No scope to close")
        restored_scope = self.prev.pop()
        self.clear()
        self.update(restored_scope)
    def extend(self,x,v): 
        if x in self:
            raise Exception("Variable '{x}' already defined")
        self[x] = v
    def lookup(self,x): 
        if x in self:
            return self[x]
        for env in self.prev:
            if x in env: return env[x]
        raise Exception("Variable '{x}' is undefined")
    def update_self(self,x,v):
        if x in self:
            self[x] = v
            return
        for env in self.prev:
            if x in env:
                env[x] = v
                return
        raise Exception("Variable '{x}' is undefined")
    def display(self, msg):
        print(msg, self, self.prev)
    def deep_copy(self):
        new_env = Env()
        for key, value in self.items():
            new_env[key] = copy.deepcopy(value) 
        new_env.prev = copy.deepcopy(self.prev)
        return new_env

env = Env()

# Closure
#
class Closure():
    def __init__(self,id,body,env):
        self.id = id
        self.body = body
        self.env = env

# Interpreter
#
@v_args(inline=True)
class Eval(Interpreter):
    def __init__(self):
        super().__init__()
        self.env = env  
    def num(self, val):  
        return int(val)

    # ... need code
    def var(self, name):
        return env.lookup(name)
    
    def decl(self, name, value):
        evaluated_value = self.visit(value)
        env.extend(name, evaluated_value)
    
    def assign(self, name, value):
        evaluated_value = self.visit(value)
        env.update_self(name, value)

    def prstmt(self, value):
        result = self.visit(value)
        print(result)

    def block(self, *stmts):
        env.openScope()
        for stmt in stmts:
            self.visit(stmt)
        env.closeScope()
    
    def ifstmt(self, condition, true_stmt, false_stmt=None):
        if condition:
            self.visit(true_stmt)
        elif false_stmt is not None:
            self.visit(false_stmt)

    def whstmt(self, condition, body):
        while condition:
            self.visit(body)

    def add(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val + right_val

    def sub(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val - right_val

    def mul(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val * right_val

    def div(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val // right_val

    def func(self, name, body):
        closure_env = env.deep_copy() 
        return Closure(name, body, closure_env)

    def call(self, func, arg):
        global env
        funcv = self.visit(func)
        argv = self.visit(arg)
        new_env = funcv.env.deep_copy()
        new_env.openScope()  
        new_env.extend(funcv.id, argv)
        temp_env = env
        env = new_env
        try:
            result = self.visit(funcv.body)
        finally:
            env = temp_env
        new_env.closeScope()
        return result

    def funcdecl(self, name, param, body):
        closure_env = env.deep_copy()
        closure = Closure(param, body, closure_env)
        env.extend(name, closure)
import sys
def main():
    try:
        prog = sys.stdin.read()
        tree = parser.parse(prog)
        print(prog, end="")
        Eval().visit(tree)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()

