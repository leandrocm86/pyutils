#!/usr/bin/env python3
"""
Interactive Frame Inspector with Textual - Mobile Responsive
Displays stack frames and their local variables in a collapsible tree with mouse support
Responsive layout: horizontal on desktop, vertical on mobile/narrow screens
"""

from textual.app import App, ComposeResult
from textual.widgets import Tree, Static, Header, Footer, Button
from textual.containers import Horizontal
from textual.binding import Binding
import traceback
import linecache
from typing import Any, Dict, Optional
from types import TracebackType


class FrameInspector(App[None]):
    """Interactive frame inspector with collapsible tree view and responsive layout"""

    CSS = """
    /* Default desktop layout */
    #main-container {
        layout: horizontal;
    }

    #tree {
        width: 50%;
        height: 1fr;
    }

    #details {
        width: 50%;
        height: 1fr;
        padding: 1;
        border: solid $primary;
        margin-left: 1;
    }

    /* Mobile layout */
    .mobile-layout #main-container {
        layout: vertical;
    }

    .mobile-layout #tree {
        width: 1fr;
        height: 60%;
    }

    .mobile-layout #details {
        width: 1fr;
        height: 40%;
        padding: 1;
        border: solid $primary;
        margin-top: 1;
        margin-left: 0;
    }

    .property-name {
        color: $accent;
        text-style: bold;
    }

    .property-type {
        color: $secondary;
        text-style: italic;
    }

    .property-value {
        color: $text;
    }

    .collection-item {
        color: $warning;
    }

    .method-signature {
        color: $success;
        text-style: italic;
    }

    .frame-info {
        color: $primary;
        text-style: bold;
    }

    .code-line {
        color: $warning;
        text-style: italic;
    }

    .exception-info {
        color: $error;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "toggle_layout", "Toggle Layout"),
        Binding("l", "change_limit", "Change Tree Limit"),
    ]

    def __init__(self, exc_traceback: Optional[TracebackType] = None,
                 exc_type: Optional[type] = None,
                 exc_value: Optional[BaseException] = None,
                 max_items: int = 50):
        super().__init__()
        self.exc_traceback = exc_traceback
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.details_panel = None
        self.main_container = None
        self.tree_widget: Tree[Any] | None = None
        self.max_items = max_items
        self.frames = self._extract_frames()
        self.selected_node = None
        self.is_mobile_layout = True
        # DON'T call self.update_layout() here - it will be called in on_mount()

    def _extract_frames(self) -> list[dict[str, Any]]:
        """Extract all frames from the traceback"""
        frames: list[dict[str, Any]] = []
        if self.exc_traceback:
            tb = self.exc_traceback
            while tb:
                frame = tb.tb_frame
                filename = frame.f_code.co_filename
                lineno = tb.tb_lineno
                func_name = frame.f_code.co_name

                # Get the actual line of code
                try:
                    code_line = linecache.getline(filename, lineno).strip()
                except Exception:
                    code_line = "<code unavailable>"

                frames.append({
                    'frame': frame,
                    'filename': filename,
                    'lineno': lineno,
                    'func_name': func_name,
                    'code_line': code_line,
                    'locals': frame.f_locals.copy(),
                    'globals': frame.f_globals
                })
                tb = tb.tb_next

        return frames

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Create initial horizontal layout
        with Horizontal(id="main-container"):
            self.tree_widget = Tree("Stack Frames", id="tree")
            self.tree_widget.show_root = True
            self.tree_widget.show_guides = True
            yield self.tree_widget

            self.details_panel = Static("Select a frame or variable to view details", id="details")
            yield self.details_panel

        yield Footer()

    def on_mount(self) -> None:
        """Setup the app when it starts"""
        self.main_container = self.query_one("#main-container")
        # Now it's safe to update the layout since the app is mounted
        self.update_layout()
        self.populate_tree()

    def update_layout(self) -> None:
        """Update the layout based on mobile/desktop mode"""
        # Just update CSS classes - let CSS handle the layout
        if self.is_mobile_layout:
            self.add_class("mobile-layout")
            self.remove_class("desktop-layout")
        else:
            self.add_class("desktop-layout")
            self.remove_class("mobile-layout")

        # Force a refresh to ensure the layout is applied correctly
        self.refresh()

    def populate_tree(self) -> None:
        """Populate the tree when the app starts"""
        if self.tree_widget:
            self.tree_widget.clear()
            self.tree_widget.root.set_label("🔍 Stack Frames")

            # Add exception info if available
            if self.exc_type and self.exc_value:
                self.tree_widget.root.add(
                    f"❌ Exception: {self.exc_type.__name__}",
                    data={
                        'type': 'exception',
                        'exc_type': self.exc_type,
                        'exc_value': self.exc_value
                    }
                )

            # Add each frame
            for i, frame_info in enumerate(self.frames):
                # Create a descriptive label for the frame
                filename = frame_info['filename'].split('/')[-1]  # Just the filename
                func_name = frame_info['func_name']
                code_line = frame_info['code_line']

                # Truncate long code lines
                if len(code_line) > 60:
                    code_line = code_line[:57] + "..."

                frame_label = f"📍 {filename}:{frame_info['lineno']} in {func_name}()"
                frame_node = self.tree_widget.root.add(
                    frame_label,
                    data={
                        'type': 'frame',
                        'frame_info': frame_info,
                        'frame_index': i
                    },
                    expand=i == len(self.frames) - 1  # Expand the last (innermost) frame
                )

                # Add code line as a sub-node
                frame_node.add(
                    f"💻 {code_line}",
                    data={
                        'type': 'code_line',
                        'frame_info': frame_info
                    }
                )

                # Add local variables
                locals_dict = frame_info['locals']
                if locals_dict:
                    locals_node = frame_node.add("📋 Local Variables", expand=False)
                    self.populate_variables_node(locals_node, locals_dict, max_depth=4)

                # Add globals (only show non-builtin ones)
                globals_dict = {k: v for k, v in frame_info['globals'].items()
                                if not k.startswith('__') and k not in ['__builtins__']}
                if globals_dict:
                    globals_node = frame_node.add("🌐 Global Variables", expand=False)
                    self.populate_variables_node(globals_node, globals_dict, max_depth=2)

            self.tree_widget.root.expand()

    def populate_variables_node(self, node: Any, variables_dict: dict[str, Any], max_depth: int = 3, current_depth: int = 0):
        """Populate a node with variables (similar to the original populate_tree_node)"""
        if current_depth >= max_depth:
            return

        # Sort variables by name
        sorted_vars = sorted(variables_dict.items(), key=lambda x: str(x[0]))

        for var_name, var_value in sorted_vars:
            var_type = type(var_value).__name__

            # Create the variable node
            var_node = node.add(
                f"{var_name}: {var_type}",
                data={
                    'type': 'variable',
                    'name': var_name,
                    'value': var_value,
                    'var_type': var_type
                }
            )

            # Add subnodes for complex types
            self.add_content_subnodes(var_node, var_value, current_depth, max_depth)

    def add_content_subnodes(self, parent_node: Any, value: Any, current_depth: int, max_depth: int):
        """Add subnodes showing the contents of complex objects (same as original)"""
        # Handle dictionaries
        if isinstance(value, dict):
            if len(value) > 0:
                if len(value) <= self.max_items:  # Show all items for small dicts
                    for key, val in value.items():
                        key_str = str(key)[:30]  # Truncate long keys
                        val_type = type(val).__name__

                        key_node = parent_node.add(
                            f'🔑 "{key_str}": {val_type}',
                            data={
                                'type': 'dict_item',
                                'name': f'[{key}]',
                                'value': val,
                                'var_type': val_type,
                                'parent_obj': value
                            }
                        )

                        # Recursively add content for nested objects
                        if current_depth < max_depth - 1:
                            self.add_content_subnodes(key_node, val, current_depth + 1, max_depth)
                else:
                    # For large dicts, show first half and last half
                    items = list(value.items())
                    half_limit = self.max_items // 2

                    # First half
                    for key, val in items[:half_limit]:
                        key_str = str(key)[:30]
                        val_type = type(val).__name__
                        parent_node.add(
                            f'🔑 "{key_str}": {val_type}',
                            data={
                                'type': 'dict_item',
                                'name': f'[{key}]',
                                'value': val,
                                'var_type': val_type,
                                'parent_obj': value
                            }
                        )

                    # Middle separator
                    hidden_count = len(value) - self.max_items
                    parent_node.add(f"... and {hidden_count} more items in between ...")

                    # Last half
                    for key, val in items[-half_limit:]:
                        key_str = str(key)[:30]
                        val_type = type(val).__name__
                        parent_node.add(
                            f'🔑 "{key_str}": {val_type}',
                            data={
                                'type': 'dict_item',
                                'name': f'[{key}]',
                                'value': val,
                                'var_type': val_type,
                                'parent_obj': value
                            }
                        )

        # Handle lists and tuples
        elif isinstance(value, (list, tuple)):
            if len(value) > 0:
                type_name = "📋" if isinstance(value, list) else "📦"

                if len(value) <= self.max_items:  # Show all items for small collections
                    for i, item in enumerate(value):
                        item_type = type(item).__name__

                        item_node = parent_node.add(
                            f'{type_name} [{i}]: {item_type}',
                            data={
                                'type': 'list_item',
                                'name': f'[{i}]',
                                'value': item,
                                'var_type': item_type,
                                'parent_obj': value
                            }
                        )

                        # Recursively add content for nested objects
                        if current_depth < max_depth - 1:
                            self.add_content_subnodes(item_node, item, current_depth + 1, max_depth)
                else:
                    # For large collections, show first half and last half
                    half_limit = self.max_items // 2

                    # First half
                    for i in range(half_limit):
                        item = value[i]
                        item_type = type(item).__name__
                        parent_node.add(
                            f'{type_name} [{i}]: {item_type}',
                            data={
                                'type': 'list_item',
                                'name': f'[{i}]',
                                'value': item,
                                'var_type': item_type,
                                'parent_obj': value
                            }
                        )

                    # Middle separator
                    hidden_count = len(value) - self.max_items
                    parent_node.add(f"... and {hidden_count} more items in between ...")

                    # Last half
                    for i in range(len(value) - half_limit, len(value)):
                        item = value[i]
                        item_type = type(item).__name__
                        parent_node.add(
                            f'{type_name} [{i}]: {item_type}',
                            data={
                                'type': 'list_item',
                                'name': f'[{i}]',
                                'value': item,
                                'var_type': item_type,
                                'parent_obj': value
                            }
                        )

        # Handle sets
        elif isinstance(value, set):
            if len(value) > 0:
                items = list(value)  # Convert to list for indexing
                display_count = min(self.max_items, len(value))

                for i in range(display_count):
                    item = items[i]
                    item_type = type(item).__name__
                    parent_node.add(
                        f'🎯 {item_type}',
                        data={
                            'type': 'set_item',
                            'name': f'set_item_{i}',
                            'value': item,
                            'var_type': item_type,
                            'parent_obj': value
                        }
                    )

                if len(value) > self.max_items:
                    parent_node.add(f"... and {len(value) - self.max_items} more items")

        # Handle custom objects with __dict__
        elif hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, type)):
            try:
                obj_dict = value.__dict__
                if obj_dict:
                    obj_node = parent_node.add("🏗️ Object Properties", expand=False)
                    self.populate_variables_node(obj_node, obj_dict, max_depth, current_depth + 1)
            except Exception:
                pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection to show details"""

        self.selected_node = event
        node = event.node

        if node.data:
            data = node.data
            details_text = self.format_details(data)
        else:
            details_text = f"[bold]{node.label}[/bold]\n\nThis is a category node."

        assert self.details_panel
        self.details_panel.update(details_text)

    def format_details(self, data: Dict) -> str:
        """Format details for different types of data"""
        data_type = data.get('type', 'unknown')

        if data_type == 'exception':
            exc_type = data['exc_type']
            exc_value = data['exc_value']
            details = "[bold red]Exception Details[/bold red]\n\n"
            details += f"[bold]Type:[/bold] {exc_type.__name__}\n"
            details += f"[bold]Message:[/bold] {str(exc_value)}\n\n"

            if hasattr(exc_value, '__traceback__') and exc_value.__traceback__:
                details += "[bold]Traceback:[/bold]\n"
                tb_lines = traceback.format_exception(exc_type, exc_value, exc_value.__traceback__)
                tb_text = ''.join(tb_lines)
                max_tb_length = 1500 if self.is_mobile_layout else 2500
                if len(tb_text) > max_tb_length:
                    details += f"{tb_text[:max_tb_length]}...\n"
                    details += "[dim](Traceback truncated)[/dim]\n"
                else:
                    details += tb_text

            return details

        elif data_type == 'frame':
            frame_info = data['frame_info']
            frame_index = data['frame_index']

            details = f"[bold cyan]Frame #{frame_index}[/bold cyan]\n\n"
            details += f"[bold]File:[/bold] {frame_info['filename']}\n"
            details += f"[bold]Line:[/bold] {frame_info['lineno']}\n"
            details += f"[bold]Function:[/bold] {frame_info['func_name']}()\n\n"
            details += f"[bold]Code:[/bold]\n{frame_info['code_line']}\n\n"

            # Show some context around the line
            try:
                context_lines = []
                start_line = max(1, frame_info['lineno'] - 2)
                end_line = frame_info['lineno'] + 3

                for line_num in range(start_line, end_line):
                    line_content = linecache.getline(frame_info['filename'], line_num).rstrip()
                    if line_content:
                        marker = ">>> " if line_num == frame_info['lineno'] else "    "
                        context_lines.append(f"{marker}{line_num:4}: {line_content}")

                if context_lines:
                    details += "[bold]Context:[/bold]\n"
                    details += "\n".join(context_lines) + "\n\n"

            except Exception:
                pass

            details += f"[bold]Local Variables:[/bold] {len(frame_info['locals'])}\n"
            details += f"[bold]Global Variables:[/bold] {len([k for k in frame_info['globals'].keys() if not k.startswith('__')])}\n"

            return details

        elif data_type == 'code_line':
            frame_info = data['frame_info']
            details = "[bold yellow]Code Line[/bold yellow]\n\n"
            details += f"[bold]File:[/bold] {frame_info['filename']}\n"
            details += f"[bold]Line {frame_info['lineno']}:[/bold]\n"
            details += f"{frame_info['code_line']}\n\n"
            return details

        elif data_type in ['variable', 'dict_item', 'list_item', 'set_item']:
            # Use the original format_property_details logic
            return self.format_property_details(data)

        else:
            return f"[bold]{data_type}[/bold]\n\nNo additional details available."

    def format_property_details(self, data: Dict) -> str:
        """Format property details for the details panel (from original code)"""
        name = data['name']
        value = data['value']
        prop_type = data['var_type']

        details = f"[bold cyan]{name}[/bold cyan]\n\n"
        details += f"[bold]Type:[/bold] [italic]{prop_type}[/italic]\n\n"

        # Show the full value
        try:
            details += "[bold]Value:[/bold]\n"

            max_display_length = 3000 if not self.is_mobile_layout else 100
            value_str = str(value)

            if len(value_str) > max_display_length:
                middle_index = max_display_length // 2
                details += f"{value_str[:middle_index]} (...) {value_str[-middle_index:]}\n\n"
                details += f"[dim](Value truncated - showing only {max_display_length} characters)[/dim]\n\n"
            else:
                details += f"{value_str}\n\n"

            # Show additional info for collections
            if isinstance(value, (list, tuple)):
                details += f"[bold]Length:[/bold] {len(value)}\n"
                if value:
                    item_types = list({type(item).__name__ for item in value[:20]})
                    details += f"[bold]Item types:[/bold] {', '.join(item_types)}\n"
            elif isinstance(value, dict):
                details += f"[bold]Keys:[/bold] {len(value)}\n"
                if value:
                    sample_keys = list(value.keys())[:5]
                    details += f"[bold]Sample keys:[/bold] {sample_keys}\n"
                    key_types = list({type(k).__name__ for k in value.keys()})
                    value_types = list({type(v).__name__ for v in value.values()})
                    details += f"[bold]Key types:[/bold] {', '.join(key_types)}\n"
                    details += f"[bold]Value types:[/bold] {', '.join(value_types)}\n"
            elif isinstance(value, set):
                details += f"[bold]Size:[/bold] {len(value)}\n"
                if value:
                    item_types = list({type(item).__name__ for item in list(value)[:10]})
                    details += f"[bold]Item types:[/bold] {', '.join(item_types)}\n"
            elif hasattr(value, '__len__'):
                try:
                    details += f"[bold]Length:[/bold] {len(value)}\n"
                except Exception:
                    pass

        except Exception as e:
            details += f"[red]Error displaying value: {e}[/red]\n"

        return details

    def action_refresh(self) -> None:
        """Refresh the tree"""
        self.populate_tree()

    def action_change_limit(self) -> None:
        """Change the limit for displaying collection items"""
        from textual.widgets import Input
        from textual.containers import Container
        from textual.screen import ModalScreen

        class LimitInputScreen(ModalScreen):
            def __init__(self, current_limit: int):
                super().__init__()
                self.current_limit = current_limit

            def compose(self) -> ComposeResult:
                with Container(id="limit-dialog"):
                    yield Static(f"Current limit: {self.current_limit}\nEnter new limit for collection items:", id="limit-label")
                    yield Input(value=str(self.current_limit), placeholder="Enter number...", id="limit-input")
                    with Horizontal():
                        yield Button("OK", variant="primary", id="ok-btn")
                        yield Button("Cancel", variant="default", id="cancel-btn")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "ok-btn":
                    try:
                        input_widget = self.query_one("#limit-input", Input)
                        new_limit = int(input_widget.value)
                        if new_limit > 0:
                            self.dismiss(new_limit)
                        else:
                            self.dismiss(None)
                    except ValueError:
                        self.dismiss(None)
                elif event.button.id == "cancel-btn":
                    self.dismiss(None)

            def on_input_submitted(self, event: Input.Submitted) -> None:
                try:
                    new_limit = int(event.value)
                    if new_limit > 0:
                        self.dismiss(new_limit)
                    else:
                        self.dismiss(None)
                except ValueError:
                    self.dismiss(None)

        def handle_limit_result(new_limit):
            if new_limit is not None:
                self.max_items = new_limit
                self.populate_tree()  # Refresh the tree with new limit

        self.push_screen(LimitInputScreen(self.max_items), handle_limit_result)

    def action_toggle_layout(self) -> None:
        """Toggle between mobile and desktop layout"""
        self.is_mobile_layout = not self.is_mobile_layout
        self.update_layout()
        if self.selected_node is not None:
            self.on_tree_node_selected(self.selected_node)


def inspect_frames(exc_traceback: Optional[TracebackType] = None,
                   exc_type: Optional[type] = None,
                   exc_value: Optional[BaseException] = None,
                   max_items: int = 50):
    """Launch the interactive frame inspector"""
    app = FrameInspector(exc_traceback, exc_type, exc_value, max_items)
    app.run()


# Example usage and demo
if __name__ == "__main__":
    # Create a sample exception to demonstrate the frame inspector
    def level3():
        local_var = "I'm in level3"  # noqa #NOSONAR
        numbers = [1, 2, 3, 4, 5]  # noqa #NOSONAR
        long_list = list(range(100))  # noqa #NOSONAR
        data = {"key": "value", "nested": {"inner": "data"}}  # noqa #NOSONAR
        raise ValueError("This is a test exception!")

    def level2():
        level2_var = "I'm in level2"  # noqa #NOSONAR
        some_list = ["a", "b", "c"]  # noqa #NOSONAR
        long_string = 'abcdefghijklmnopqrstuvwyxz' * 100  # noqa #NOSONAR
        level3()  # This will raise the exception

    def level1():
        level1_var = "I'm in level1"  # noqa #NOSONAR
        important_data = {"status": "running", "count": 42}  # noqa #NOSONAR
        long_list_of_big_strings = ["a" * 1000 for _ in range(100)]  # noqa #NOSONAR
        level2()

    try:
        level1()
    except Exception:
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()

        print("Frame Inspector Demo")
        print("This will show all frames in the call stack with their local variables")
        print("Navigate using mouse or keyboard, press 'q' to quit")
        print()

        inspect_frames(exc_traceback, exc_type, exc_value)
