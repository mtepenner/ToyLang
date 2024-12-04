# Matthew Penner
#

# CS358 Fall'24 Assignment 4 (Part A)
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
    def num(self, val):  return int(val)

    # ... need code
    def var(self, name):
        if name not in self.env:
            raise ValueError(f"Variable '{name}' is not defined.")
        return self.env[name]
    
    def decl(self, name, value):
        self.env[name] = self.visit(value)
    
    def prstmt(self, value):
        print(self.visit(value))

    def block(self, *stmts):
        for stmt in stmts:
            self.visit(stmt)
    
    def add(self, left, right):
        return self.visit(left) + self.visit(right)

    def sub(self, left, right):
        return self.visit(left) - self.visit(right)

    def mul(self, left, right):
        return self.visit(left) * self.visit(right)

    def div(self, left, right):
        return self.visit(left) // self.visit(right)

    def func(self, name, body):
        return Closure(name, body, env.deep_copy())

    def call(self, func, arg):
        func = self.visit(func)
        temp_env = self.env
        self.env = func.env
        self.env.openScope()
        self.env.extend(func.id, self.visit(arg))
        result = self.visit(func.body)
        self.env.closeScope()
        self.env = temp_env
        return result
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

