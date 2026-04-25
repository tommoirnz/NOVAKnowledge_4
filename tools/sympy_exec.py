import subprocess
import sys

def sympy_exec(code: str, log_callback=None) -> str:
    """
    Execute SymPy code and return the result.
    Use this to verify or compute mathematics symbolically.
    The code should be valid Python using SymPy.
    Example: 'from sympy import *\\nx=symbols(\"x\")\\nprint(integrate(x**2,x))'
    """
    try:
        if log_callback:
            log_callback(f"[SYMPY] Executing SymPy code...")
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip() or "No output"
        else:
            return f"SymPy Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: SymPy timed out after 15 seconds"
    except Exception as e:
        return f"Error: {str(e)}"