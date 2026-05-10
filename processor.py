import time

class MacroProcessor:
    def __init__(self):
        self.mnt = {}  # Macro Name Table
        self.mdt = []  # Macro Definition Table
        self.expanded_code = []
        self.errors = []
        self.logs = [] # Execution Logger
        self.symbol_table = {} # Symbol Name -> Memory Address
        self.macros_used = set() # To track dead code
        
        self.keywords = {"READ", "WRITE", "ADD", "SUB", "STORE", "START", "STOP"}
        self.current_memory_address = 1000 # Starting mock memory address
        
        self.execution_tree = []
        
        self.stats = {
            "macros_defined": 0,
            "original_lines": 0,
            "expanded_lines": 0,
            "time_taken_ms": 0,
            "expansion_ratio": 0.0,
            "unused_macros": 0
        }

    def process(self, source_code):
        start_time = time.time()
        
        self.mnt = {}
        self.mdt = []
        self.expanded_code = []
        self.errors = []
        self.logs = []
        self.symbol_table = {}
        self.macros_used = set()
        self.current_memory_address = 1000
        self.execution_tree = []
        
        lines = source_code.split('\n')
        self.stats["original_lines"] = len(lines)
        
        self.logs.append("⚙️ Starting Pass 1: Scanning for Macro Definitions...")
        
        # Pass 1: Identify macro definitions
        in_macro = False
        macro_name = ""
        params = []
        macro_start_line = 0
        
        pass2_lines = [] 
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                if not in_macro:
                    pass2_lines.append((line_num, line))
                continue

            tokens = line.strip().split()

            if tokens[0] == "MACRO":
                if in_macro:
                    self.errors.append({"line": line_num, "msg": "Nested macro definitions are not supported.", "fix": "Remove the inner MACRO definition."})
                    self.logs.append(f"❌ Pass 1 Error: Nested MACRO definition at line {line_num}.")
                in_macro = True
                macro_name = ""
                macro_start_line = line_num
                continue

            if in_macro:
                if not macro_name:
                    macro_name = tokens[0]
                    if macro_name in self.mnt:
                        self.errors.append({"line": line_num, "msg": f"Duplicate Macro Name '{macro_name}'.", "fix": "Rename the macro to a unique name."})
                        self.logs.append(f"❌ Pass 1 Error: Duplicate Macro '{macro_name}' at line {line_num}.")
                    
                    param_str = " ".join(tokens[1:]).replace(',', ' ')
                    params = param_str.split()
                    
                    self.mnt[macro_name] = {"index": len(self.mdt), "params": len(params)}
                    self.mdt.append(line.strip())
                    self.logs.append(f"📌 Pass 1: Registered Macro '{macro_name}' with {len(params)} parameter(s) at line {line_num}.")
                elif tokens[0] == "MEND":
                    self.mdt.append("MEND")
                    in_macro = False
                else:
                    body_line = line.strip()
                    for i, param in enumerate(params, 1):
                        body_line = body_line.replace(param, f"#{i}")
                    self.mdt.append(body_line)
            else:
                pass2_lines.append((line_num, line))
                    
        if in_macro:
            self.errors.append({"line": macro_start_line, "msg": "Missing MEND", "fix": "Add a 'MEND' instruction at the end of the macro definition."})

        self.stats["macros_defined"] = len(self.mnt)
        self.logs.append(f"✅ Pass 1 Complete: Found {len(self.mnt)} Macro(s).")

        if self.errors:
            self.logs.append("🛑 Halting before Pass 2 due to Pass 1 errors.")
            return self._get_result(start_time)

        self.logs.append("🚀 Starting Pass 2: Expanding macros and resolving symbols...")
        # Pass 2: Expand macro calls (Recursive Support)
        self._expand_lines(pass2_lines, call_stack=[], tree_list=self.execution_tree)
        
        # Post-processing stats
        self.stats["expanded_lines"] = len(self.expanded_code)
        
        # Dead code detection
        unused = set(self.mnt.keys()) - self.macros_used
        self.stats["unused_macros"] = len(unused)
        if unused:
            self.logs.append(f"⚠️ Warning: Found {len(unused)} unused macro(s): {', '.join(unused)}")
            
        self.logs.append(f"🏁 Pass 2 Complete: Expanded to {self.stats['expanded_lines']} lines.")
            
        return self._get_result(start_time)

    def _register_symbol(self, token):
        if token and token not in self.keywords and token not in self.mnt and not token.startswith('#') and not token.isdigit():
            # Remove any trailing commas or noise if they somehow persisted
            clean_token = token.strip(',')
            if clean_token not in self.symbol_table:
                self.symbol_table[clean_token] = self.current_memory_address
                self.logs.append(f"🔤 Symbol Table: Registered '{clean_token}' at Address {self.current_memory_address}")
                self.current_memory_address += 4 # Assume 4-byte word size for realism

    def _expand_lines(self, pass2_lines, call_stack, tree_list):
        for line_num, line in pass2_lines:
            if not line.strip():
                self.expanded_code.append(line)
                continue

            tokens = line.strip().split()

            # Register symbols in regular code
            if tokens[0] in self.keywords:
                for token in tokens[1:]:
                    self._register_symbol(token)

            # Identify macro call
            if tokens[0] in self.mnt:
                macro_name = tokens[0]
                actual_args = " ".join(tokens[1:]).replace(',', ' ').split()
                args_str = ", ".join(actual_args)
                
                macro_node = {
                    "type": "macro",
                    "name": macro_name,
                    "args": args_str,
                    "substitution": [],
                    "children": [],
                    "mdt_range": None
                }
                tree_list.append(macro_node)
                
                self.logs.append(f"🔄 Expanding Macro '{macro_name}' from line {line_num}")
                self._expand_macro_call(macro_name, tokens[1:], line_num, call_stack, macro_node)
                
            elif tokens[0] in self.keywords:
                self.expanded_code.append(line.strip())
                tree_list.append({
                    "type": "instruction",
                    "text": line.strip()
                })
            else:
                # Undefined Macro Call
                self.errors.append({"line": line_num, "msg": f"Undefined Macro Call or Keyword '{tokens[0]}'.", "fix": "Check for typos or ensure the macro is defined before calling."})
                self.expanded_code.append(line.strip())
                tree_list.append({
                    "type": "error",
                    "text": f"ERROR: {tokens[0]}"
                })

    def _expand_macro_call(self, macro_name, args, call_line_num, call_stack, macro_node):
        # Infinite Recursion Check
        if macro_name in call_stack:
            chain = " -> ".join(call_stack + [macro_name])
            self.errors.append({"line": call_line_num, "msg": f"Infinite Recursion Detected: {chain}", "fix": "Remove cyclic macro calls."})
            self.logs.append(f"🔥 FATAL: Infinite Recursion aborted ({chain}).")
            macro_node["children"].append({
                "type": "recursion",
                "text": "INFINITE RECURSION HALT"
            })
            return
            
        self.macros_used.add(macro_name)
        new_call_stack = call_stack + [macro_name]

        expected_params = self.mnt[macro_name]["params"]
        mdt_idx = self.mnt[macro_name]["index"]
        
        param_str = " ".join(args).replace(',', ' ')
        actual_params = param_str.split()
        
        if len(actual_params) != expected_params:
            self.errors.append({"line": call_line_num, "msg": f"Mismatched Parameter Count for '{macro_name}'. Expected {expected_params}, got {len(actual_params)}.", "fix": f"Pass exactly {expected_params} arguments."})
            macro_node["children"].append({
                "type": "error",
                "text": "PARAMETER MISMATCH ERROR"
            })
            return
        
        curr_mdt_idx = mdt_idx + 1
        macro_node["mdt_range"] = [curr_mdt_idx, None]
        expanded_lines_to_process = []
        
        while curr_mdt_idx < len(self.mdt) and self.mdt[curr_mdt_idx] != "MEND":
            original_line = self.mdt[curr_mdt_idx]
            expanded_line = original_line
            for i, act_param in enumerate(actual_params, 1):
                expanded_line = expanded_line.replace(f"#{i}", act_param)
            
            macro_node["substitution"].append(f"{original_line}  →  {expanded_line}")
            expanded_lines_to_process.append((call_line_num, expanded_line))
            curr_mdt_idx += 1
            
        macro_node["mdt_range"][1] = curr_mdt_idx - 1
            
        # Recursively expand the lines to support nested macro calls
        self._expand_lines(expanded_lines_to_process, new_call_stack, macro_node["children"])


    def _get_result(self, start_time):
        end_time = time.time()
        self.stats["time_taken_ms"] = round((end_time - start_time) * 1000, 2)
        if self.stats["original_lines"] > 0:
            self.stats["expansion_ratio"] = round(self.stats["expanded_lines"] / self.stats["original_lines"], 2)
            
        return {
            "mnt": self.mnt,
            "mdt": self.mdt,
            "symbol_table": self.symbol_table,
            "expanded_code": "\n".join(self.expanded_code),
            "errors": self.errors,
            "logs": self.logs,
            "execution_tree": self.execution_tree,
            "stats": self.stats,
            "unused_macros": list(set(self.mnt.keys()) - self.macros_used)
        }
