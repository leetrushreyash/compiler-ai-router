"""Code extraction utilities for snippet retrieval."""
from pathlib import Path
from typing import List, Tuple, Optional


class CodeExtractor:
    """Extract code snippets from source files."""
    
    @staticmethod
    def get_line_range(
        filepath: str, 
        start_line: int, 
        end_line: int,
        context_lines: int = 3
    ) -> str:
        """
        Get code snippet with optional context.
        
        Args:
            filepath: Path to source file
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)
            context_lines: Number of context lines before/after
            
        Returns:
            Code snippet as string
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return f"# File not found: {filepath}"
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Adjust indices (convert from 1-indexed to 0-indexed)
        start = max(0, start_line - context_lines - 1)
        end = min(len(lines), end_line + context_lines)
        
        snippet_lines = lines[start:end]
        return ''.join(snippet_lines)
    
    @staticmethod
    def get_exact_line(filepath: str, line_number: int) -> Optional[str]:
        """Get a specific line from file."""
        filepath = Path(filepath)
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                if i == line_number:
                    return line.rstrip('\n')
        
        return None
    
    @staticmethod
    def get_function_snippet(filepath: str, start_line: int, length: int = 10) -> str:
        """Get function/method snippet."""
        return CodeExtractor.get_line_range(filepath, start_line, start_line + length - 1)


if __name__ == "__main__":
    # Example usage
    extractor = CodeExtractor()
    # snippet = extractor.get_line_range("sample.py", 10, 20)
    # print(snippet)
