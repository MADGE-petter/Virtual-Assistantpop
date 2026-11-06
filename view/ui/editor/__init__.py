"""POP Code Editor Package."""
from view.ui.editor.code_highlighter import CodeHighlighter
from view.ui.editor.code_editor_widget import CodeEditorWidget
from view.ui.editor.editor_tab_widget import EditorTabWidget
from view.ui.editor.project_explorer_widget import ProjectExplorerWidget
from view.ui.editor.embedded_terminal_widget import EmbeddedTerminalWidget
from view.ui.editor.ai_coding_panel import AICodingPanel
from view.ui.editor.code_editor_window import CodeEditorStudioWidget, CodeEditorWindow

__all__ = [
    "CodeHighlighter",
    "CodeEditorWidget",
    "EditorTabWidget",
    "ProjectExplorerWidget",
    "EmbeddedTerminalWidget",
    "AICodingPanel",
    "CodeEditorStudioWidget",
    "CodeEditorWindow",
]
