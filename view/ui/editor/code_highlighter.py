"""Syntax Highlighter for CodeEditorWidget.
Supports multi-language syntax highlighting using QRegularExpression and
a cyber dark OneDark / Monokai palette aligned with POP Assistant aesthetics.
"""
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class CodeHighlighter(QSyntaxHighlighter):
    """Multi-language regex-based syntax highlighter."""

    def __init__(self, parent=None, language: str = "python"):
        super().__init__(parent)
        self.language = language.lower()
        self.highlighting_rules = []
        self._setup_palette()
        self.set_language(self.language)

    def _setup_palette(self):
        # Monokai Cyber / OneDark Pro palette
        self.fmt_keyword = QTextCharFormat()
        self.fmt_keyword.setForeground(QColor("#C678DD"))  # Purple
        self.fmt_keyword.setFontWeight(QFont.Weight.Bold)

        self.fmt_builtin = QTextCharFormat()
        self.fmt_builtin.setForeground(QColor("#00CCFF"))  # Electric Cyan

        self.fmt_type = QTextCharFormat()
        self.fmt_type.setForeground(QColor("#E5C07B"))  # Amber Gold

        self.fmt_string = QTextCharFormat()
        self.fmt_string.setForeground(QColor("#00FFAA"))  # Emerald Green

        self.fmt_number = QTextCharFormat()
        self.fmt_number.setForeground(QColor("#D19A66"))  # Peach / Orange

        self.fmt_comment = QTextCharFormat()
        self.fmt_comment.setForeground(QColor("#6B7280"))  # Muted grey
        self.fmt_comment.setFontItalic(True)

        self.fmt_decorator = QTextCharFormat()
        self.fmt_decorator.setForeground(QColor("#56B6C2"))  # Teal

        self.fmt_operator = QTextCharFormat()
        self.fmt_operator.setForeground(QColor("#E06C75"))  # Coral Red

        self.fmt_tag = QTextCharFormat()
        self.fmt_tag.setForeground(QColor("#E06C75"))  # Red/Pink tag
        self.fmt_tag.setFontWeight(QFont.Weight.Bold)

        self.fmt_attr = QTextCharFormat()
        self.fmt_attr.setForeground(QColor("#D19A66"))  # Orange attribute

    def set_language(self, language: str):
        self.language = language.lower()
        self.highlighting_rules.clear()

        if self.language in ("py", "python"):
            self._setup_python_rules()
        elif self.language in ("js", "jsx", "ts", "tsx", "javascript", "typescript"):
            self._setup_js_rules()
        elif self.language in ("html", "htm", "xml", "svg"):
            self._setup_html_rules()
        elif self.language in ("css", "scss", "less"):
            self._setup_css_rules()
        elif self.language in ("json",):
            self._setup_json_rules()
        elif self.language in ("c", "cpp", "h", "hpp", "cxx", "cs"):
            self._setup_cpp_rules()
        elif self.language in ("sh", "bash", "ps1", "powershell"):
            self._setup_shell_rules()
        elif self.language in ("md", "markdown"):
            self._setup_markdown_rules()
        else:
            self._setup_generic_rules()

        self.rehighlight()

    def _setup_python_rules(self):
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
            "or", "pass", "raise", "return", "try", "while", "with", "yield"
        ]
        for kw in keywords:
            pattern = QRegularExpression(rf"\b{kw}\b")
            self.highlighting_rules.append((pattern, self.fmt_keyword))

        builtins = [
            "self", "cls", "True", "False", "None", "print", "len", "range",
            "int", "float", "str", "list", "dict", "set", "tuple", "bool",
            "super", "isinstance", "type", "open", "enumerate", "zip", "map"
        ]
        for b in builtins:
            pattern = QRegularExpression(rf"\b{b}\b")
            self.highlighting_rules.append((pattern, self.fmt_builtin))

        # Decorators (@decorator)
        self.highlighting_rules.append((QRegularExpression(r"@[A-Za-z0-9_]+"), self.fmt_decorator))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), self.fmt_number))

        # Strings ("..." or '...')
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.fmt_string))

        # Single line comment (# ...)
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), self.fmt_comment))

    def _setup_js_rules(self):
        keywords = [
            "const", "let", "var", "function", "return", "if", "else", "for", "while",
            "do", "switch", "case", "break", "continue", "default", "import", "export",
            "from", "class", "extends", "super", "this", "new", "async", "await",
            "try", "catch", "finally", "throw", "typeof", "instanceof", "in", "of"
        ]
        for kw in keywords:
            self.highlighting_rules.append((QRegularExpression(rf"\b{kw}\b"), self.fmt_keyword))

        builtins = [
            "true", "false", "null", "undefined", "NaN", "console", "window",
            "document", "Math", "JSON", "Promise", "Array", "Object", "String", "Number"
        ]
        for b in builtins:
            self.highlighting_rules.append((QRegularExpression(rf"\b{b}\b"), self.fmt_builtin))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), self.fmt_number))

        # Strings (`...`, "...", '...')
        self.highlighting_rules.append((QRegularExpression(r"`[^`\\]*(\\.[^`\\]*)*`"), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.fmt_string))

        # Comments (// ... and /* ... */)
        self.highlighting_rules.append((QRegularExpression(r"//[^\n]*"), self.fmt_comment))
        self.highlighting_rules.append((QRegularExpression(r"/\*.*?\*/"), self.fmt_comment))

    def _setup_html_rules(self):
        # Tags <tag> or </tag>
        self.highlighting_rules.append((QRegularExpression(r"</?[A-Za-z0-9_-]+"), self.fmt_tag))
        self.highlighting_rules.append((QRegularExpression(r"/?>"), self.fmt_tag))
        # Attributes
        self.highlighting_rules.append((QRegularExpression(r"\b[a-zA-Z-]+(?==)"), self.fmt_attr))
        # Strings
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), self.fmt_string))
        # Comments
        self.highlighting_rules.append((QRegularExpression(r"<!--.*?-->"), self.fmt_comment))

    def _setup_css_rules(self):
        # Properties
        self.highlighting_rules.append((QRegularExpression(r"\b[a-zA-Z-]+(?=\s*:)"), self.fmt_builtin))
        # Selectors / Classes / IDs
        self.highlighting_rules.append((QRegularExpression(r"[.#][A-Za-z0-9_-]+"), self.fmt_type))
        # Numbers & Units
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(px|em|rem|%|vh|vw|s|ms)?\b"), self.fmt_number))
        # Colors #fff, #ffffff
        self.highlighting_rules.append((QRegularExpression(r"#[0-9a-fA-F]{3,8}\b"), self.fmt_string))
        # Strings
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), self.fmt_string))
        # Comments
        self.highlighting_rules.append((QRegularExpression(r"/\*.*?\*/"), self.fmt_comment))

    def _setup_json_rules(self):
        # Keys ("key":)
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"(?=\s*:)'), self.fmt_type))
        # String values
        self.highlighting_rules.append((QRegularExpression(r':\s*"[^"\\]*(\\.[^"\\]*)*"'), self.fmt_string))
        # Booleans / null
        self.highlighting_rules.append((QRegularExpression(r"\b(true|false|null)\b"), self.fmt_keyword))
        # Numbers
        self.highlighting_rules.append((QRegularExpression(r"\b-?[0-9]+(\.[0-9]+)?\b"), self.fmt_number))

    def _setup_cpp_rules(self):
        keywords = [
            "auto", "break", "case", "catch", "class", "const", "continue", "default",
            "delete", "do", "else", "enum", "explicit", "export", "extern", "for",
            "friend", "goto", "if", "inline", "mutable", "namespace", "new", "noexcept",
            "operator", "private", "protected", "public", "return", "sizeof", "static",
            "struct", "switch", "template", "this", "throw", "try", "typedef", "typename",
            "union", "using", "virtual", "void", "volatile", "while"
        ]
        for kw in keywords:
            self.highlighting_rules.append((QRegularExpression(rf"\b{kw}\b"), self.fmt_keyword))

        types = ["int", "float", "double", "char", "bool", "long", "short", "unsigned", "signed", "size_t", "uint32_t", "int64_t"]
        for t in types:
            self.highlighting_rules.append((QRegularExpression(rf"\b{t}\b"), self.fmt_type))

        # Preprocessor (#include, #define)
        self.highlighting_rules.append((QRegularExpression(r"#[A-Za-z0-9_]+"), self.fmt_decorator))
        # Numbers
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?[fFlLuU]?\b"), self.fmt_number))
        # Strings
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.fmt_string))
        # Comments
        self.highlighting_rules.append((QRegularExpression(r"//[^\n]*"), self.fmt_comment))
        self.highlighting_rules.append((QRegularExpression(r"/\*.*?\*/"), self.fmt_comment))

    def _setup_shell_rules(self):
        keywords = ["if", "then", "else", "elif", "fi", "case", "esac", "for", "while", "until", "do", "done", "in", "function"]
        for kw in keywords:
            self.highlighting_rules.append((QRegularExpression(rf"\b{kw}\b"), self.fmt_keyword))
        # Variables $VAR or ${VAR}
        self.highlighting_rules.append((QRegularExpression(r"\$[A-Za-z0-9_]+"), self.fmt_type))
        # Strings
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), self.fmt_string))
        # Comments
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), self.fmt_comment))

    def _setup_markdown_rules(self):
        # Headers (# H1, ## H2)
        self.highlighting_rules.append((QRegularExpression(r"^#{1,6}\s+[^\n]*"), self.fmt_keyword))
        # Bold **text**
        self.highlighting_rules.append((QRegularExpression(r"\*\*[^*]+\*\*"), self.fmt_type))
        # Code block `code`
        self.highlighting_rules.append((QRegularExpression(r"`[^`]+`"), self.fmt_string))
        # Links [text](url)
        self.highlighting_rules.append((QRegularExpression(r"\[[^\]]+\]\([^)]+\)"), self.fmt_builtin))

    def _setup_generic_rules(self):
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.fmt_string))
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), self.fmt_number))
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*|//[^\n]*"), self.fmt_comment))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

