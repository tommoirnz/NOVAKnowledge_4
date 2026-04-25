# ==================== MATH-TO-SPEECH CLASS ====================

import re
from typing import List, Tuple, Dict


class MathSpeechConverter:
    """
    A comprehensive class for converting LaTeX math notation to spoken English.
    Handles inline and block math, symbols, functions, matrices, integrals, and more.
    """

    def __init__(self):
        # Math symbol mappings
        self._math_symbol_subs = [
            # Basic operators
            (r'\\cdot\b', ' dot '), (r'\\times\b', ' times '), (r'\\div\b', ' divided by '),
            (r'\\pm\b', ' plus or minus '), (r'\\mp\b', ' minus or plus '),

            # Relations
            (r'\\leq?\b', ' less than or equal to '), (r'\\geq?\b', ' greater than or equal to '),
            (r'\\neq\b', ' not equal to '), (r'\\approx\b', ' approximately '),
            (r'\\sim\b', ' similar to '), (r'\\propto\b', ' proportional to '),
            (r'\\equiv\b', ' equivalent to '),

            # Calculus and analysis
            (r'\\infty\b', ' infinity '), (r'\\partial\b', ' partial '), (r'\\nabla\b', ' nabla '),
            (r'\\grad\b', ' gradient '), (r'\\curl\b', ' curl '), (r'\\divergence\b', ' divergence '),

            # Set theory
            (r'\\in\b', ' in '), (r'\\notin\b', ' not in '), (r'\\subset\b', ' subset of '),
            (r'\\subseteq\b', ' subset of or equal to '), (r'\\cup\b', ' union '), (r'\\cap\b', ' intersection '),
            (r'\\emptyset\b', ' empty set '),

            # Logic
            (r'\\forall\b', ' for all '), (r'\\exists\b', ' there exists '), (r'\\land\b', ' and '),
            (r'\\lor\b', ' or '), (r'\\neg\b', ' not '), (r'\\implies\b', ' implies '),
            (r'\\iff\b', ' if and only if '),

            # Arrows
            (r'\\to\b', ' to '), (r'\\rightarrow\b', ' right arrow '), (r'\\leftarrow\b', ' left arrow '),
            (r'\\Rightarrow\b', ' implies '), (r'\\Leftarrow\b', ' implied by '),

            # Common functions
            (r'\\sin\b', ' sine '), (r'\\cos\b', ' cosine '), (r'\\tan\b', ' tangent '),
            (r'\\cot\b', ' cotangent '), (r'\\sec\b', ' secant '), (r'\\csc\b', ' cosecant '),
            (r'\\arcsin\b', ' arc sine '), (r'\\arccos\b', ' arc cosine '), (r'\\arctan\b', ' arc tangent '),
            (r'\\sinh\b', ' hyperbolic sine '), (r'\\cosh\b', ' hyperbolic cosine '),
            (r'\\tanh\b', ' hyperbolic tangent '),
            (r'\\log\b', ' log '), (r'\\ln\b', ' natural log '), (r'\\exp\b', ' exponential '),
            (r'\\det\b', ' determinant '), (r'\\trace\b', ' trace '), (r'\\rank\b', ' rank '),

            # Special functions
            (r'\\lim\b', ' limit '), (r'\\max\b', ' maximum '), (r'\\min\b', ' minimum '),
            (r'\\sup\b', ' supremum '), (r'\\inf\b', ' infimum '), (r'\\arg\b', ' argument '),

            # Vector/tensor notation
            (r'\\vec\s*\{([^}]+)\}', r'vector \1'), (r'\\mathbf\s*\{([^}]+)\}', r'bold \1'),
            (r'\\mathbb\s*\{([^}]+)\}', r'blackboard \1'), (r'\\mathcal\s*\{([^}]+)\}', r'calligraphic \1'),
            (r'\\hat\s*\{([^}]+)\}', r'hat \1'), (r'\\tilde\s*\{([^}]+)\}', r'tilde \1'),
        ]

        # Greek letters
        self._math_greek_letters = {
            # Lowercase
            "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta",
            "epsilon": "epsilon", "varepsilon": "epsilon", "zeta": "zeta", "eta": "eta",
            "theta": "theta", "vartheta": "theta", "iota": "iota", "kappa": "kappa",
            "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi",
            "omicron": "omicron", "pi": "pi", "varpi": "pi", "rho": "rho",
            "varrho": "rho", "sigma": "sigma", "varsigma": "sigma", "tau": "tau",
            "upsilon": "upsilon", "phi": "phi", "varphi": "phi", "chi": "chi",
            "psi": "psi", "omega": "omega",

            # Uppercase
            "Gamma": "capital gamma", "Delta": "capital delta", "Theta": "capital theta",
            "Lambda": "capital lambda", "Xi": "capital xi", "Pi": "capital pi",
            "Sigma": "capital sigma", "Upsilon": "capital upsilon", "Phi": "capital phi",
            "Psi": "capital psi", "Omega": "capital omega",
        }

        # Matrix environments
        self._math_matrix_envs = {
            'pmatrix': 'parentheses matrix', 'bmatrix': 'bracket matrix', 'Bmatrix': 'brace matrix',
            'vmatrix': 'determinant matrix', 'Vmatrix': 'double bar matrix', 'matrix': 'matrix',
        }

        # Regex patterns
        self._math_block_pat = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        self._math_inline_pat = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', re.DOTALL)

        # Strip macros
        self._math_strip_macros = [
            r'\\left', r'\\right', r'\\,', r'\\;', r'\\:', r'\\!', r'\\quad', r'\\qquad',
            r'\\mathrm', r'\\mathit', r'\\operatorname', r'\\big', r'\\Big', r'\\bigg', r'\\Bigg',
        ]

    # ── Add these two new methods to MathSpeechConverter ──────────────────────

    def _extract_braced(self, s: str, start: int):
        """Extract content of {…} at position start (must be '{').
        Returns (inner_content, index_after_closing_brace)."""
        assert s[start] == '{', f"Expected '{{' at pos {start}, got {s[start]!r}"
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    return s[start + 1:i], i + 1
        return s[start + 1:], len(s)  # unclosed brace fallback

    def _speakify_frac(self, s: str) -> str:
        """Nested-brace-aware \\frac{num}{den} → 'num over den'.
        Recurses so nested fracs work correctly."""
        for _ in range(12):  # iterate until no more \\frac found
            pos = s.find('\\frac')
            if pos == -1:
                break
            i = pos + 5
            # skip optional whitespace
            while i < len(s) and s[i] in ' \t\n':
                i += 1
            if i >= len(s) or s[i] != '{':
                break  # malformed — leave it alone

            num_raw, i = self._extract_braced(s, i)

            while i < len(s) and s[i] in ' \t\n':
                i += 1
            if i >= len(s) or s[i] != '{':
                break

            den_raw, i = self._extract_braced(s, i)

            # Recurse so nested \frac inside num/den also converts
            num_spoken = self._speakify_frac(num_raw.strip())
            den_spoken = self._speakify_frac(den_raw.strip())

            s = s[:pos] + f'{num_spoken} over {den_spoken}' + s[i:]
        return s

    def _apply_pairs(self, s: str, pairs: List[Tuple[str, str]]) -> str:
        """Apply regex substitutions"""
        for pat, repl in pairs:
            s = re.sub(pat, repl, s)
        return s

    def _strip_nested(self, s, command):
        result = []
        i = 0
        cmd = command + '{'
        while i < len(s):
            pos = s.find(cmd, i)
            if pos == -1:
                result.append(s[i:]);
                break
            result.append(s[i:pos])
            depth = 0
            j = pos + len(command)
            start = j
            while j < len(s):
                if s[j] == '{':
                    depth += 1
                elif s[j] == '}':
                    depth -= 1
                    if depth == 0:
                        result.append(s[start + 1:j])
                        i = j + 1;
                        break
                j += 1
            else:
                result.append(s[pos:]);
                break
        return ''.join(result)

    def convert_math_to_speech(self, tex: str) -> str:
        if not tex.strip():
            return 'empty expression'

        s = tex

        # Strip boxing wrappers (nested-brace-aware)
        for cmd in ['\\boxed', '\\underline', '\\overline', '\\underbrace', '\\overbrace']:
            for _ in range(4):
                prev = s
                result = []
                i = 0
                search = cmd + '{'
                while i < len(s):
                    pos = s.find(search, i)
                    if pos == -1:
                        result.append(s[i:])
                        break
                    result.append(s[i:pos])
                    depth = 0
                    j = pos + len(cmd)
                    start = j
                    while j < len(s):
                        if s[j] == '{':
                            depth += 1
                        elif s[j] == '}':
                            depth -= 1
                            if depth == 0:
                                result.append(s[start + 1:j])
                                i = j + 1
                                break
                        j += 1
                    else:
                        result.append(s[pos:])
                        break
                s = ''.join(result)
                if s == prev:
                    break

        # Simplify \log{x} → \log x etc before frac processing
        s = re.sub(r'(\\(?:log|ln|sin|cos|tan|arctan|arcsin|arccos|exp))\s*\{([^{}]+)\}', r'\1 \2', s)

        # Strip \left \right
        s = re.sub(r'\\left\s*[\(\[\{]', '(', s)
        s = re.sub(r'\\right\s*[\)\]\}]', ')', s)

        # Handle matrices first
        s = self._speakify_matrix(s)

        # Handle integrals, differentials, summations, limits
        s = self._speakify_integral(s)
        s = self._speakify_differential(s)
        s = self._speakify_summation(s)
        s = self._speakify_limits(s)

        # Handle roots
        for _ in range(6):
            s2 = re.sub(r'\\sqrt\[(.+?)\]\{([^{}]+)\}', r'\1-th root of \2', s)
            s2 = re.sub(r'\\sqrt\s*\{([^{}]+)\}', r'square root of \1', s2)
            if s2 == s:
                break
            s = s2

        # ── KEY FIX: fractions FIRST while braces are still intact ──────────
        # _speakify_frac is nested-brace-aware so \frac{\frac{a}{b}}{c} works
        s = self._speakify_frac(s)

        # Exponents and subscripts AFTER fracs so inner braces weren't clobbered
        s = re.sub(r'\^\{([^}]+)\}', r' to the power of \1', s)
        s = re.sub(r'_\{([^}]+)\}', r' sub \1', s)
        s = re.sub(r'_([A-Za-z0-9])', r' sub \1', s)

        # Handle Greek letters
        for greek, spoken in self._math_greek_letters.items():
            s = re.sub(rf'\\{greek}\b', spoken, s)

        # Apply symbol substitutions
        s = self._apply_pairs(s, self._math_symbol_subs)

        # Strip unnecessary macros
        for macro in self._math_strip_macros:
            s = re.sub(macro + r'\b', '', s)

        # Clean up remaining braces, backslashes, and bare operators
        s = s.replace('{', '').replace('}', '').replace('\\', '')
        s = s.replace('=', ' equals ')
        s = s.replace('+', ' plus ')
        s = s.replace('-', ' minus ')
        s = s.replace('*', ' times ')
        s = s.replace('/', ' divided by ')

        # Handle simple powers (squared/cubed) and differential pronunciation
        s = self._fix_simple_powers(s)
        s = self._fix_differential_pronunciation(s)

        # Normalize whitespace
        s = re.sub(r'\s+', ' ', s).strip()

        return s or 'mathematical expression'



    def _speakify_matrix(self, tex: str) -> str:
        """Convert matrix environments to spoken description"""
        for env, spoken_name in self._math_matrix_envs.items():
            if f'\\begin{{{env}}}' in tex:
                # Extract matrix content and describe it
                matrix_content = re.sub(r'\\begin\{[^}]*\}|\\end\{[^}]*\}|\\\\|&', ' ', tex)
                matrix_content = re.sub(r'\s+', ' ', matrix_content).strip()
                return f'{spoken_name} containing {matrix_content}'
        return tex

    def _speakify_integral(self, tex: str) -> str:
        """Convert integral notation — handles missing bounds gracefully."""

        def _fmt(prefix, m):
            lo = m.group(1)  # may be None if group didn't match
            hi = m.group(2)
            if lo and hi:
                return f'{prefix} from {lo} to {hi} of'
            elif lo:
                return f'{prefix} over {lo} of'
            return f'{prefix} of'

        tex = re.sub(
            r'\\iiint(?:\s*_\s*\{([^}]+)\})?(?:\s*\^\s*\{([^}]+)\})?',
            lambda m: _fmt('triple integral', m), tex)
        tex = re.sub(
            r'\\iint(?:\s*_\s*\{([^}]+)\})?(?:\s*\^\s*\{([^}]+)\})?',
            lambda m: _fmt('double integral', m), tex)
        tex = re.sub(
            r'\\oint(?:\s*_\s*\{([^}]+)\})?(?:\s*\^\s*\{([^}]+)\})?',
            lambda m: _fmt('closed integral', m), tex)
        tex = re.sub(
            r'\\int(?:\s*_\s*\{([^}]+)\})?(?:\s*\^\s*\{([^}]+)\})?',
            lambda m: _fmt('integral', m), tex)
        return tex


    def _speakify_differential(self, tex: str) -> str:
        """Convert differential notation to spoken form"""
        tex = re.sub(r'\\frac\{\s*\\partial\s*\}\{\s*\\partial\s*([^}]+)\s*\}',
                     r'partial derivative with respect to \1', tex)
        tex = re.sub(r'\\frac\{\s*d\s*\}\{\s*d\s*([^}]+)\s*\}', r'derivative with respect to \1', tex)
        tex = re.sub(r'\\dot\s*\{([^}]+)\}', r'\1 dot', tex)
        tex = re.sub(r'\\ddot\s*\{([^}]+)\}', r'\1 double dot', tex)

        # NEW: Handle standalone differentials like du, dv before other processing
        tex = re.sub(r'\b(\\?d[uvxyz])\b', lambda m: ' '.join(m.group(1).replace('\\', '')), tex)

        return tex

    def _speakify_summation(self, tex: str) -> str:
        """Convert summation notation to spoken form"""
        tex = re.sub(r'\\sum\s*_\s*\{([^}]+)\}\s*\^\s*\{([^}]+)\}', r'sum from \1 to \2 of', tex)
        tex = re.sub(r'\\sum\s*_\s*\{([^}]+)\}', r'sum over \1 of', tex)
        tex = re.sub(r'\\sum\b', 'sum of', tex)
        return tex

    def _speakify_limits(self, tex: str) -> str:
        """Convert limit notation to spoken form"""
        tex = re.sub(r'\\lim\s*_\s*\{([^}]+)\s*\\to\s*([^}]+)\}', r'limit as \1 approaches \2 of', tex)
        tex = re.sub(r'\\lim\b', 'limit of', tex)
        return tex

    def _fix_differential_pronunciation(self, s: str) -> str:
        """Convert du → d u, dx → d x, etc."""
        s = re.sub(r'\b(d[uvxyz])\b', lambda m: ' '.join(m.group(1)), s)
        s = re.sub(r'([∂Δ])([a-zA-Z])', r'\1 \2', s)
        return s

    def _fix_simple_powers(self, s: str) -> str:
        """Convert powers to natural speech"""
        # Handle squared and cubed first
        s = re.sub(r'([a-zA-Zα-ωΑ-Ω])\s*\^\s*2\b', r'\1 squared', s)
        s = re.sub(r'([a-zA-Zα-ωΑ-Ω])\s*\^\s*3\b', r'\1 cubed', s)
        s = re.sub(r'(\d+)\s*\^\s*2\b', r'\1 squared', s)
        s = re.sub(r'(\d+)\s*\^\s*3\b', r'\1 cubed', s)

        # Then handle other simple powers (letters and numbers)
        s = re.sub(r'([a-zA-Zα-ωΑ-Ω])\s*\^\s*([A-Za-z0-9])', r'\1 to the power of \2', s)
        s = re.sub(r'(\d+)\s*\^\s*([A-Za-z0-9])', r'\1 to the power of \2', s)

        return s





    def _normalize_delimiters(self, s: str) -> str:
        """Normalize LaTeX delimiters"""
        s = s.replace('\r\n', '\n')
        s = re.sub(r'\\\s*\$\$', '$$', s)
        s = re.sub(r'\\\s*\$', '$', s)
        s = re.sub(r'\\\(\s*(.*?)\s*\\\)', lambda m: f"${m.group(1).strip()}$", s, flags=re.DOTALL)
        s = re.sub(r'\\\[\s*(.*?)\s*\\\]', lambda m: f"$${m.group(1).strip()}$$", s, flags=re.DOTALL)
        return s

    def _extract_math_tokens(self, s: str):
        """Extract math content and replace with tokens"""
        tokens = []

        def _repl_block(m):
            tokens.append(m.group(1))
            return f'<<<MATH{len(tokens) - 1}>>>'

        s = self._math_block_pat.sub(_repl_block, s)

        def _repl_inline(m):
            tokens.append(m.group(1))
            return f'<<<MATH{len(tokens) - 1}>>>'

        s = self._math_inline_pat.sub(_repl_inline, s)
        return s, tokens

    def make_speakable_text(self, text: str, speak_math: bool = True) -> str:
        """
        Convert text with LaTeX math to speakable text

        Args:
            text: Input text containing LaTeX math
            speak_math: If True, convert math to speech; if False, say "equation"

        Returns:
            Text ready for TTS
        """
        t = (text or "")

        # Remove code blocks
        while '```' in t:
            a = t.find('```')
            b = t.find('```', a + 3)
            if b == -1: break
            t = t[:a] + ' [code block] ' + t[b + 3:]

        t = t.replace('`', ' ')

        # Normalize delimiters and extract math
        t = self._normalize_delimiters(t)
        base, tokens = self._extract_math_tokens(t)

        # Convert math tokens
        if speak_math:
            spoken = [self.convert_math_to_speech(tex) for tex in tokens]
        else:
            spoken = ['equation' for _ in tokens]

        # Replace tokens with spoken versions
        for i, sp in enumerate(spoken):
            base = base.replace(f'<<<MATH{i}>>>', sp)

        # Clean up formatting
        base = re.sub(r'(?m)^\s{0,3}#{1,6}\s*', '', base)
        base = re.sub(r'(?m)^\s{0,3}[*\-+]\s+', '', base)
        base = base.replace('#', '').replace('*', '').replace('_', ' ')
        base = base.replace('&', ' and ').replace('\\', ' ')

        # Final cleanup
        base = re.sub(r'\s+', ' ', base).strip()

        return base or "[silence]"

