"""Control flow analysis for code smell detection."""
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import re


BRANCH_KEYWORDS = {'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with'}
TERMINATOR_KEYWORDS = {'return', 'break', 'continue', 'raise'}


@dataclass
class BasicBlock:
    """Represents a basic block in control flow."""
    block_id: int
    statements: List[str]
    successors: List[int] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    block_type: str = "sequential"  # sequential, branch, loop, exception, exit
    indent_level: int = 0


class ControlFlowAnalyzer:
    """Analyzes control flow in code."""
    
    def __init__(self):
        self.blocks: Dict[int, BasicBlock] = {}
        self.block_counter = 0
    
    def analyze_function(self, code: str) -> Dict[str, any]:
        """
        Analyze control flow of a function.
        
        Args:
            code: Function code to analyze
            
        Returns:
            Control flow analysis results
        """
        self.blocks = {}
        self.block_counter = 0
        
        # Extract basic blocks and wire up edges
        self._extract_basic_blocks(code)
        self._wire_edges()
        
        # Calculate metrics
        results = {
            "block_count": len(self.blocks),
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(),
            "unreachable_code": self._detect_unreachable_code(),
            "data_dependencies": self._analyze_data_dependencies(code),
            "cfg_edges": self._get_edge_list(),
        }
        
        return results
    
    def _get_indent_level(self, line: str) -> int:
        """Get indentation level (number of leading spaces / 4)."""
        stripped = line.lstrip()
        if not stripped:
            return 0
        return (len(line) - len(stripped)) // 4

    def _classify_block(self, first_stmt: str) -> str:
        """Classify block type based on its first statement."""
        s = first_stmt.strip()
        if s.startswith(('if ', 'elif ')):
            return "branch"
        elif s.startswith(('for ', 'while ')):
            return "loop"
        elif s.startswith(('try:', 'except', 'finally')):
            return "exception"
        elif s.startswith(('return', 'raise', 'break', 'continue')):
            return "exit"
        elif s.startswith('else'):
            return "branch"
        return "sequential"

    def _extract_basic_blocks(self, code: str):
        """Extract basic blocks from code, tracking indent levels."""
        lines = code.strip().split('\n')
        current_stmts: List[str] = []
        current_indent = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            indent = self._get_indent_level(line)
            is_leader = any(stripped.startswith(kw) for kw in BRANCH_KEYWORDS)
            is_terminator = any(stripped.startswith(kw) for kw in TERMINATOR_KEYWORDS)
            
            # Start new block on branch keyword or indentation change
            if is_leader or (current_stmts and indent != current_indent):
                if current_stmts:
                    blk = self._create_block(current_stmts, current_indent)
                    self._store_block(blk)
                current_stmts = [stripped]
                current_indent = indent
            else:
                current_stmts.append(stripped)
                current_indent = indent
            
            # End block after a terminator statement
            if is_terminator:
                blk = self._create_block(current_stmts, current_indent)
                self._store_block(blk)
                current_stmts = []
        
        if current_stmts:
            blk = self._create_block(current_stmts, current_indent)
            self._store_block(blk)

    def _wire_edges(self):
        """Wire successor/predecessor edges between basic blocks."""
        block_ids = sorted(self.blocks.keys())
        if not block_ids:
            return
        
        for i, bid in enumerate(block_ids):
            block = self.blocks[bid]
            btype = block.block_type
            first_stmt = block.statements[0] if block.statements else ""
            last_stmt = block.statements[-1] if block.statements else ""
            
            # Exit blocks (return/raise) have no fallthrough
            if any(last_stmt.startswith(kw) for kw in TERMINATOR_KEYWORDS):
                # Look for sibling blocks at same indent (else/except/finally)
                if first_stmt.startswith(('if ', 'elif ')):
                    for j in range(i + 1, len(block_ids)):
                        next_blk = self.blocks[block_ids[j]]
                        ns = next_blk.statements[0] if next_blk.statements else ""
                        if ns.startswith(('elif ', 'else')):
                            self._add_edge(bid, block_ids[j])
                            break
                continue
            
            # Branch: if/elif connects to body (next block) and to elif/else sibling
            if first_stmt.startswith(('if ', 'elif ')):
                # True branch: falls through to next block (the body)
                if i + 1 < len(block_ids):
                    self._add_edge(bid, block_ids[i + 1])
                
                # False branch: skip to matching elif/else/end at same or lower indent
                for j in range(i + 1, len(block_ids)):
                    cand = self.blocks[block_ids[j]]
                    cs = cand.statements[0] if cand.statements else ""
                    if cand.indent_level <= block.indent_level:
                        if cs.startswith(('elif ', 'else')):
                            self._add_edge(bid, block_ids[j])
                        elif cand.indent_level < block.indent_level or \
                             not cs.startswith(('elif ', 'else')):
                            # Merge point after the entire if-chain
                            self._add_edge(bid, block_ids[j])
                        break
            
            # Loop: for/while connects to body and to first block after loop
            elif first_stmt.startswith(('for ', 'while ')):
                # Loop body = next block
                if i + 1 < len(block_ids):
                    self._add_edge(bid, block_ids[i + 1])
                # Loop exit: find block at same or lower indent after body
                for j in range(i + 1, len(block_ids)):
                    cand = self.blocks[block_ids[j]]
                    if cand.indent_level <= block.indent_level and j > i + 1:
                        self._add_edge(bid, block_ids[j])
                        # Back edge: loop body last block goes back to loop header
                        if block_ids[j - 1] in self.blocks:
                            prev_blk = self.blocks[block_ids[j - 1]]
                            pl = prev_blk.statements[-1] if prev_blk.statements else ""
                            if not any(pl.startswith(kw) for kw in TERMINATOR_KEYWORDS):
                                self._add_edge(block_ids[j - 1], bid)
                        break
            
            # else block: connect to body
            elif first_stmt.startswith(('else:', 'else')):
                if i + 1 < len(block_ids):
                    self._add_edge(bid, block_ids[i + 1])
            
            # try/except/finally: wire to next block
            elif first_stmt.startswith(('try:', 'except', 'finally')):
                if i + 1 < len(block_ids):
                    self._add_edge(bid, block_ids[i + 1])
                # try also connects to except
                if first_stmt.startswith('try:'):
                    for j in range(i + 1, len(block_ids)):
                        cand = self.blocks[block_ids[j]]
                        cs = cand.statements[0] if cand.statements else ""
                        if cs.startswith('except'):
                            self._add_edge(bid, block_ids[j])
                            break
            
            # Sequential: fallthrough to next block
            else:
                if i + 1 < len(block_ids):
                    self._add_edge(bid, block_ids[i + 1])
    
    def _add_edge(self, from_id: int, to_id: int):
        """Add a directed edge between two blocks."""
        if to_id not in self.blocks[from_id].successors:
            self.blocks[from_id].successors.append(to_id)
        if from_id not in self.blocks[to_id].predecessors:
            self.blocks[to_id].predecessors.append(from_id)
    
    def _get_edge_list(self) -> List[Tuple[int, int]]:
        """Return all CFG edges as (from, to) tuples."""
        edges = []
        for bid, block in self.blocks.items():
            for succ in block.successors:
                edges.append((bid, succ))
        return edges
    
    def _create_block(self, statements: List[str], indent: int = 0) -> BasicBlock:
        """Create a new basic block."""
        block_id = self.block_counter
        self.block_counter += 1
        btype = self._classify_block(statements[0]) if statements else "sequential"
        return BasicBlock(
            block_id=block_id,
            statements=statements,
            successors=[],
            predecessors=[],
            block_type=btype,
            indent_level=indent,
        )
    
    def _store_block(self, block: BasicBlock):
        """Store a basic block."""
        self.blocks[block.block_id] = block
    
    def _calculate_cyclomatic_complexity(self) -> float:
        """Calculate cyclomatic complexity from CFG.  M = E - N + 2P."""
        edges = sum(len(block.successors) for block in self.blocks.values())
        nodes = len(self.blocks)
        
        if nodes == 0:
            return 1.0
        
        # M = E - N + 2P, where P = 1 (single connected component)
        return max(1.0, edges - nodes + 2)
    
    def _detect_unreachable_code(self) -> List[int]:
        """Detect unreachable blocks via BFS from entry block."""
        if not self.blocks:
            return []
        
        entry_id = min(self.blocks.keys())
        reachable: Set[int] = set()
        queue = [entry_id]
        
        while queue:
            block_id = queue.pop(0)
            if block_id in reachable:
                continue
            
            reachable.add(block_id)
            if block_id in self.blocks:
                queue.extend(self.blocks[block_id].successors)
        
        # Unreachable blocks
        return [bid for bid in self.blocks.keys() if bid not in reachable]
    
    def _analyze_data_dependencies(self, code: str) -> Dict[str, List[str]]:
        """Analyze data dependencies in code."""
        dependencies = {}
        
        # Extract variable definitions and uses
        defines = re.findall(r'(\w+)\s*=(?!=)', code)
        uses = re.findall(r'(?<![=!<>])\b([a-z_]\w*)\b(?!\s*=)', code)
        
        for var in set(defines):
            var_uses = [u for u in uses if u == var]
            dependencies[var] = var_uses
        
        return dependencies


class DataFlowAnalyzer:
    """Analyzes data flow in code."""
    
    def __init__(self):
        self.use_def_chains: Dict[str, List[Tuple[int, int]]] = {}
    
    def analyze(self, code: str) -> Dict[str, any]:
        """
        Analyze data flow.
        
        Args:
            code: Code to analyze
            
        Returns:
            Data flow analysis results
        """
        lines = code.split('\n')
        
        results = {
            "tainted_variables": self._find_tainted_variables(code),
            "uninitialized_uses": self._find_uninitialized_uses(code),
            "unused_definitions": self._find_unused_definitions(code),
        }
        
        return results
    
    def _find_tainted_variables(self, code: str) -> List[Dict[str, any]]:
        """Find potentially tainted (untrusted) variables."""
        tainted = []
        
        # Patterns that create tainted data
        patterns = [
            (r'input\s*\(', 'user_input'),
            (r'argv', 'command_line_arg'),
            (r'request\.\w+', 'http_request'),
            (r'socket\.\w+', 'network_input'),
        ]
        
        for pattern, source_type in patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_no = code[:match.start()].count('\n') + 1
                tainted.append({
                    "line": line_no,
                    "source": source_type,
                    "code": match.group()
                })
        
        return tainted
    
    def _find_uninitialized_uses(self, code: str) -> List[Dict[str, any]]:
        """Find uses of potentially uninitialized variables."""
        lines = code.split('\n')
        defined = set()
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Track definitions
            defines = re.findall(r'(\w+)\s*=', line)
            for var in defines:
                defined.add(var)
            
            # Track uses
            uses = re.findall(r'\b([a-z_]\w*)\b(?!\s*=)', line)
            for var in uses:
                if var not in defined and not self._is_builtin(var):
                    issues.append({
                        "line": i,
                        "variable": var,
                    })
        
        return issues
    
    def _find_unused_definitions(self, code: str) -> List[Dict[str, any]]:
        """Find definitions that are never used."""
        lines = code.split('\n')
        unused = []
        
        # Find all definitions
        definitions = {}
        for i, line in enumerate(lines, 1):
            defines = re.findall(r'(\w+)\s*=', line)
            for var in defines:
                if var not in definitions:
                    definitions[var] = i
        
        # Check which are used
        all_code = '\n'.join(lines)
        for var, def_line in definitions.items():
            # Count uses after definition
            code_after = '\n'.join(lines[def_line:])
            uses = len(re.findall(rf'\b{var}\b', code_after))
            
            if uses <= 1:  # Only the definition itself
                unused.append({
                    "line": def_line,
                    "variable": var,
                })
        
        return unused
    
    @staticmethod
    def _is_builtin(name: str) -> bool:
        """Check if name is a Python builtin."""
        builtins = {'print', 'len', 'range', 'str', 'int', 'list', 'dict', 'set', 'tuple', 'open', 'file'}
        return name in builtins


if __name__ == "__main__":
    # Example usage
    analyzer = ControlFlowAnalyzer()
    code = """
if x > 0:
    y = 10
else:
    y = 20
print(y)
"""
    result = analyzer.analyze_function(code)
    print(result)
