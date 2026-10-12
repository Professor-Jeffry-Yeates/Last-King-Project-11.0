__version__="8.0"
import ast
class NodeVisitorClass(ast.NodeVisitor):
    """
    AST visitor that only allows a safe subset of Python syntax.
    Bing Copilot helped me write this code."""
    SAFE_NODES = (
        ast.Module, ast.Expr, ast.Load, ast.Constant, ast.Name, ast.AugAssign, ast.type_ignore, ast.Pass,
        ast.BinOp, ast.UnaryOp, ast.Lt, ast.Gt, ast.LtE, ast.GtE, ast.Eq, ast.NotEq, ast.IfExp,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv, ast.USub, ast.UAdd, ast.Subscript, 
        ast.Slice,ast.Dict, ast.List, ast.Tuple, ast.Is, ast.Not, ast.And, ast.Or,
        ast.Assign, ast.Store, ast.Import, ast.alias, ast.Call, ast.Attribute,
        ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.BitOr, ast.BitAnd, ast.BitXor,
        ast.Compare, ast.If, ast.While, ast.For, ast.ExceptHandler,
        ast.Try, ast.Break, ast.Continue, ast.Pass, ast.match_case, 
        ast.Match, ast.withitem, ast.With, ast.Return, ast.In, ast.JoinedStr, ast.FormattedValue)

    SAFE_NAMES = {"a", "b", "c", "x", "y", "z", "int", "bool","float","sum","min","max"}  # Allowed variables, functions
    
    def __init__(self, *args):
        pass # ast.NodeVisitor.__init__()

    def setVariables(self, variables=None):
        self.variableNames = set()
        if variables is not None and len(variables) > 0:
            if isinstance(variables, list):
                for var in variables:
                    self.SAFE_NAMES.add(var)
                    self.variableNames.add(var)
            else:   
                self.SAFE_NAMES.add(variables)
                self.variableNames.add(variables)

    def setNodes(self, nodeNames=None):
        return # Currently no nodes to check
        if nodeNames is not None:
            safeNodesAsList = list(self.SAFE_NODES)
            #if isinstance(nodeNames, list) or isinstance(nodeNames, tuple):
            #    for node in nodeNames:
            #        if node == "os":
            #            safeNodesAsList.append(ast.AugAssign)
            #elif nodeNames == "os":
            #        safeNodesAsList.append(ast.AugAssign)
            #safeNodesAsList.append(ast.)
            self.SAFE_NODES = tuple(safeNodesAsList)
    
    def visit(self, node):
        if not isinstance(node, self.SAFE_NODES):
            raise ValueError(f"Disallowed syntax: {type(node).__name__}")
        super().visit(node) # Continue visiting child nodes in ast.NodeVisitor

    def visit_Name(self, node):
        if node.id not in self.SAFE_NAMES:
            if node.id not in self.variableNames:
                raise ValueError(f"Disallowed variable: {node.id}")
        self.generic_visit(node)
            
    def safe_exec(self, user_code, imports, required, variables):
        """
        Creates sanitized Python code in a restricted environment.
        """
        # Exclude forbidden words in the corrected code
        self.setVariables(variables)
        self.setNodes(required)

        listing = user_code.splitlines()
        for exclude in ['import', 'as', 'exec', 'eval', 'os', 'sys', '__', 'from', 'lambda', ';', '//',"#"]:
            lineNumber = 2
            for line in listing:
                lineNumber += 1
                forbiddenError = False
                if line.find(exclude) >= 0:
                    if exclude in required:
                        if exclude == "lambda":
                            temp = list(self.SAFE_NODES)
                            temp.append(ast.Lambda)
                            self.SAFE_NODES = tuple(temp)
                    else:
                        forbiddenError = True
                if forbiddenError:
                    raise ValueError(f"Forbidden keyword {exclude} near line {lineNumber} used: {exclude}")
                    
        # Place any dictionary import(s)) into the start of the code to run. The keyword "import is provided only for the first item"
        runningCode = ""
        importList = []
        if imports is not None and len(imports) > 0:
            if isinstance(imports, list) or isinstance(imports, tuple):
                for item in imports:
                    importList.append(item.strip())

            else:
                importList.append(imports.strip())
            firstImport = "import "
            for item in importList:
                runningCode += firstImport+item+"\n" 
                firstImport = ""  # Only use "import" for the first item    
        runningCode += user_code
        
        #  Make all provided imports safe (exclude anything beginning with "import" or "from")
        if len(importList) > 0:
            for item in importList:
                safeList = item.split(',')
                for item in safeList:
                    safeItem = item.strip()
                    testItem = safeItem.lower()
                    if testItem.startswith("import") or testItem.startswith("from"):
                        pass
                    else:
                        self.SAFE_NAMES.add(safeItem)
        try:
            # Parse into AST
            tree = ast.parse(runningCode, mode='exec')

        except Exception as e:
            raise ValueError(f"Unsafe or invalid code in making the code tree: {e}")
    
        try:
            # Validate AST
            self.visit(tree)

        except Exception as e:
            raise ValueError(f"Unsafe or invalid code in visit tree: {e}")

        try:    
            code = compile(tree, filename="<safe_exec>", mode="exec")
    
        except Exception as e:
            raise ValueError(f"Unsafe or invalid code when compiling the code: {e}")
        
        return code