import datetime
import enum
import inspect
import os
import sys
from pathlib import Path
import atexit

# --- Configuration (can be changed by user before first log) ---
OUTPUT_DIRECTORY = "logs/"
"""Directory where log files will be saved."""

DISPLAY_OBJECT_LIFE_TIME = True
"""Global flag to enable/disable object lifetime logging (DOLT* functions)."""

EST_FUNCTION_LENGTH = 70
"""Estimated function name length for formatting log lines.
This refers to the target width of the field containing:
TypeIndicator + Padding + FunctionName in the C++ version's specific formatting.
In this Python version, it influences the padding calculations for the function name field.
"""

SHORTER_FUNCTION_FILL_CHARACTER = ' '
"""Character used to pad function names if they are shorter than EST_FUNCTION_LENGTH."""

CONTENT_SPACE = 10
"""Number of characters for the space between the function name area and the log message content."""

CONTENT_SPACE_CHARACTER = ' '
"""Character used to create the space between function name area and content."""

SPACE_BETWEEN_CONTENT_SPACE_AND_CONTENT = True
"""If True, adds a single space character before and after the CONTENT_SPACE block."""

# --- Enums ---
class LogLevel(enum.Enum):
    """Defines the different levels of logging."""
    INFO = "INFO"
    WARNING = "WARN"
    ERROR = "ERR " # Padded to align with others if desired, C++ used "E ### ###"
    DEBUG = "DEBUG"
    RAW = "RAW"

class LogAction(enum.Flag):
    """Defines actions to be taken for a log message (Print, Save, add to Session)."""
    NONE = 0
    SAVE = enum.auto()
    PRINT = enum.auto()
    SESSION = enum.auto()
    SAVE_PRINT = SAVE | PRINT
    SAVE_SESSION = SAVE | SESSION
    PRINT_SESSION = PRINT | SESSION
    ALL = SAVE | PRINT | SESSION

# --- Global Action Modifiers (similar to C++ actionForceHighest/Lowest) ---
ACTION_FORCE_HIGHEST = LogAction.ALL
"""Ensures only defined flags in LogAction.ALL are effective."""
ACTION_FORCE_LOWEST = LogAction.NONE
"""Currently unused in Python logic, as default is ALL or specific."""


class Log:
    """
    Main logging class, implemented as a singleton.
    Handles formatting, printing, saving to file, and session logging.
    """
    _instance = None
    _log_file_handler = None
    _log_file_path = None
    _current_session_data = [] # Stores log messages for the current session

    def __init__(self):
        if Log._instance is not None:
            # This path should ideally not be taken if get_instance() is used correctly.
            pass # Or raise an error for direct instantiation attempt after singleton created.
        
        self._action_force_highest = ACTION_FORCE_HIGHEST
        self._action_force_lowest = ACTION_FORCE_LOWEST # Not actively used but kept for parity idea
        
        # Register a cleanup function to be called upon Python interpreter exit
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Closes the log file if it's open, ensuring data is flushed."""
        if Log._log_file_handler:
            try:
                Log._log_file_handler.flush()
                Log._log_file_handler.close()
            except Exception as e:
                print(f"Error during log cleanup: {e}", file=sys.stderr)
            Log._log_file_handler = None

    @classmethod
    def get_instance(cls):
        """Accesses the singleton instance of the Log class."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_timestamp(self, simple_separators: bool = False) -> str:
        """Generates a formatted timestamp string."""
        now = datetime.datetime.now()
        if simple_separators:
            # Format: YYYYMMDD_HHMMSS_ms
            return now.strftime("%Y%m%d_%H%M%S_") + f"{now.microsecond // 1000:03d}"
        else:
            # Format: YYYY-MM-DD HH:MM:SS.ms
            return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"

    def _build_prefix(self, level: LogLevel, func_name: str) -> str:
        """
        Constructs the prefix for a log line, including level, function name, and spacing.
        This attempts to replicate the C++ version's formatting logic.
        """
        level_indicator_map = {
            LogLevel.INFO:    "I ",
            LogLevel.WARNING: "W ###", # Kept from C++ for similar look
            LogLevel.ERROR:   "E ### ###", # Kept from C++ for similar look
            LogLevel.DEBUG:   "D ",
            LogLevel.RAW:     "R "
        }
        level_indicator_str = level_indicator_map.get(level, "? ")

        # C++ logic:
        # prefix = type_indicator
        # if(funName.length() >= EST_FUNCTION_LENGTH) { prefix += funName; }
        # else {
        #   fill = EST_FUNCTION_LENGTH - funName.length() - prefix.size();
        #   if(fill < 1) fill = 1; // or 0 if no space
        #   prefix += std::string(fill, SHORTER_FUNCTION_FILL_CHARACTER);
        #   prefix += funName;
        # }
        # This means EST_FUNCTION_LENGTH is the target for the (type_indicator + padding + func_name) part.
        
        combined_header_part: str
        if len(func_name) >= EST_FUNCTION_LENGTH: # This condition from C++ is a bit ambiguous.
                                                  # Interpreting EST_FUNCTION_LENGTH as a threshold for func_name's own length.
            combined_header_part = level_indicator_str + func_name
        else:
            # Calculate fill needed for (level_indicator + fill_chars + func_name) to reach EST_FUNCTION_LENGTH
            fill_needed = EST_FUNCTION_LENGTH - len(func_name) - len(level_indicator_str)
            
            if fill_needed < 0:
                fill_needed = 0 # No space for fill, or func_name + indicator is already too long
            
            # The C++ `if(fill < 1) fill = 1;` logic:
            # This ensures at least one fill char if the calculation results in 0 but space is expected.
            # For simplicity here, if fill_needed is 0, no fill_chars. If negative, also no fill_chars.
            # If specific C++ minimum fill=1 behavior is strictly needed, it can be added.
            
            fill_chars = SHORTER_FUNCTION_FILL_CHARACTER * fill_needed
            combined_header_part = level_indicator_str + fill_chars + func_name
            
        # Append content separator
        spacer_parts = []
        if SPACE_BETWEEN_CONTENT_SPACE_AND_CONTENT:
            spacer_parts.append(" ")
        spacer_parts.append(CONTENT_SPACE_CHARACTER * CONTENT_SPACE)
        if SPACE_BETWEEN_CONTENT_SPACE_AND_CONTENT:
            spacer_parts.append(" ")
        
        return combined_header_part + "".join(spacer_parts)

    def _build_start_prefix(self) -> str:
        """Builds the "APPLICATION STARTED" banner for new log files."""
        start_text = "--- [APPLICATION STARTED] ---"
        # Approximate total width based on typical log line structure for padding calculation
        approx_total_width = len("I ") + EST_FUNCTION_LENGTH + \
                             (1 if SPACE_BETWEEN_CONTENT_SPACE_AND_CONTENT else 0) + \
                             CONTENT_SPACE + \
                             (1 if SPACE_BETWEEN_CONTENT_SPACE_AND_CONTENT else 0)
        
        current_ts = self._get_timestamp()
        # Calculate padding to center the start_text within the approximate width
        padding_len = (approx_total_width - len(start_text) - len(current_ts) - 2) // 2 # -2 for "[]"
        if padding_len < 0: padding_len = 0
        
        padding_str = '-' * padding_len
        return f"[{current_ts}] {padding_str}{start_text}{padding_str}"

    def _ensure_file_open(self):
        """Ensures the log file is open. Creates directory and file if they don't exist."""
        if Log._log_file_handler is None:
            try:
                Path(OUTPUT_DIRECTORY).mkdir(parents=True, exist_ok=True)
                log_file_name_ts = self._get_timestamp(simple_separators=True)
                Log._log_file_path = Path(OUTPUT_DIRECTORY) / f"{log_file_name_ts}.log"
                
                Log._log_file_handler = open(Log._log_file_path, "a", encoding="utf-8")
                start_message = self._build_start_prefix()
                Log._log_file_handler.write(start_message + "\n")
                Log._log_file_handler.flush()
            except IOError as e:
                print(f"Error creating/opening log file '{Log._log_file_path}': {e}", file=sys.stderr)
                sys.stderr.flush()
                Log._log_file_handler = None # Reset if opening failed

    def _print_log(self, content: str, new_line: bool = True):
        """Prints log content to standard output."""
        print(content, end="\n" if new_line else "", flush=True)

    def _save_log(self, full_line_content: str):
        """Saves log content to the file. Ensures file is open."""
        self._ensure_file_open()
        if Log._log_file_handler:
            try:
                Log._log_file_handler.write(full_line_content + "\n")
                Log._log_file_handler.flush() # Important for saving if app crashes
            except IOError as e:
                print(f"Error writing to log file '{Log._log_file_path}': {e}. Content: {full_line_content}", file=sys.stderr)
                sys.stderr.flush()

    def _add_to_session(self, content: str, new_line: bool = True):
        """Adds log content to the in-memory session log."""
        Log._current_session_data.append(content + ("\n" if new_line else ""))

    def _log(self, level: LogLevel, func_name: str, message: str, action: LogAction):
        """Core logging method that dispatches to print, save, and session."""
        # Apply forced action limits (C++ parity: (action | lowest) & highest)
        effective_action = (action | LogAction.NONE) & self._action_force_highest
        
        timestamp_str = f"[{self._get_timestamp()}] " # For file logs
        
        if level == LogLevel.RAW:
            # Raw logs have specific formatting and handling
            if LogAction.PRINT in effective_action:
                self._print_log(message, new_line=False) # C++ raw print has no newline
            
            if LogAction.SAVE in effective_action:
                # C++ Raw save: time + prefix + "\n<<START RAW>>\n" + log + "\n<<END RAW>>"
                # The prefix for raw in C++ `buildPrefix` is "R ". `func_name` is used.
                raw_file_prefix = self._build_prefix(LogLevel.RAW, func_name if func_name else "raw_log")
                full_raw_message_for_file = \
                    f"{timestamp_str}{raw_file_prefix}\n<<START RAW>>\n{message}\n<<END RAW>>"
                self._save_log(full_raw_message_for_file) # _save_log adds its own final newline
            
            if LogAction.SESSION in effective_action:
                self._add_to_session(message, new_line=False) # C++ raw session has no newline
        else:
            # Standard log levels
            line_prefix = self._build_prefix(level, func_name)
            
            message_for_print_session = f"{line_prefix}{message}"
            message_for_file = f"{timestamp_str}{line_prefix}{message}"

            if LogAction.PRINT in effective_action:
                self._print_log(message_for_print_session, new_line=True)
            
            if LogAction.SAVE in effective_action:
                self._save_log(message_for_file)
            
            if LogAction.SESSION in effective_action:
                self._add_to_session(message_for_print_session, new_line=True)

    # --- Public API for logging ---
    def info(self, func_name: str, message: str, action: LogAction = LogAction.ALL):
        self._log(LogLevel.INFO, func_name, message, action)

    def warning(self, func_name: str, message: str, action: LogAction = LogAction.ALL):
        self._log(LogLevel.WARNING, func_name, message, action)

    def error(self, func_name: str, message: str, action: LogAction = LogAction.ALL):
        self._log(LogLevel.ERROR, func_name, message, action)

    def debug(self, func_name: str, message: str, action: LogAction = LogAction.ALL):
        self._log(LogLevel.DEBUG, func_name, message, action)

    def raw(self, func_name: str, message: str, action: LogAction = LogAction.ALL):
        # For raw, func_name might be a generic placeholder or the actual caller.
        self._log(LogLevel.RAW, func_name, message, action)

    def get_current_session(self) -> str:
        """Returns the accumulated log messages for the current session as a single string."""
        return "".join(Log._current_session_data)

# --- Global Logger Instance & Convenience Functions (Pythonic Macro Replacements) ---
_log_instance = Log.get_instance()

def _get_caller_func_name(depth: int = 2) -> str:
    """Utility to get the name of the calling function."""
    try:
        # depth=1: current func; depth=2: caller of this func's caller
        return inspect.stack()[depth].function
    except IndexError:
        return "unknown_function"
    except Exception: # Catch any other potential errors from inspect
        return "error_inspecting_stack"


def s_printf(message_or_format_string: any, *args) -> str:
    """
    A simple string formatting function, similar to C's sprintf.
    Uses Python's %-formatting. For new code, f-strings or .format() are preferred.
    Ensures that the output is always a string, converting non-string single arguments
    to their string representation (like print()).
    """
    if not args:
        # If no arguments for formatting, convert the first parameter to its string representation.
        # To handles cases like R(request_object) -> str(request_object)
        return str(message_or_format_string)
    
    # If args are present, message_or_format_string is expected to be a format string (str type).
    if not isinstance(message_or_format_string, str):
        # This indicates incorrect usage if s_printf is intended for string formatting like C's asprintf.
        # In this scenario, to behave somewhat like print(non_string, arg1, arg2, ...),
        # we can join the string representations of all items.
        all_items_as_strings = [str(message_or_format_string)] + [str(arg) for arg in args]
        # Adding a note about the improper usage for easier debugging.
        return " ".join(all_items_as_strings) + " [S_PRINTF_WARNING: Non-string format string used with arguments]"

    try:
        # Attempt standard %-style string formatting.
        return message_or_format_string % args
    except TypeError:
        # Fallback if formatting fails (e.g., type mismatch, wrong number of arguments).
        # To provide a useful output, we'll join string representations of the format string and all arguments.
        # This mimics a simple concatenation if formatting specifiers are problematic.
        all_items_as_strings = [str(message_or_format_string)] + [str(arg) for arg in args]
        return " ".join(all_items_as_strings) + " [S_PRINTF_ERROR: Formatting failed, fallback to concatenation]"



# Convenience logging functions similar to C++ macros I, W, E, D, R
def I(message_format: str, *args, action: LogAction = LogAction.ALL):
    """Log an INFO message. `message_format` can include %-style placeholders for `args`."""
    final_message = s_printf(message_format, *args)
    _log_instance.info(_get_caller_func_name(), final_message, action)

def W(message_format: str, *args, action: LogAction = LogAction.ALL):
    """Log a WARNING message."""
    final_message = s_printf(message_format, *args)
    _log_instance.warning(_get_caller_func_name(), final_message, action)

def E(message_format: str, *args, action: LogAction = LogAction.ALL):
    """Log an ERROR message."""
    final_message = s_printf(message_format, *args)
    _log_instance.error(_get_caller_func_name(), final_message, action)

def D(message_format: str, *args, action: LogAction = LogAction.ALL):
    """Log a DEBUG message."""
    final_message = s_printf(message_format, *args)
    _log_instance.debug(_get_caller_func_name(), final_message, action)

def R(message_format: str, *args, action: LogAction = LogAction.ALL):
    """Log a RAW message. `func_name` will be the caller of R()."""
    final_message = s_printf(message_format, *args)
    _log_instance.raw(_get_caller_func_name(), final_message, action)

# The _A versions (IA, WA etc.) from C++ can be achieved by simply passing the 'action'
# parameter to the Python functions I, W, E, D, R. For example:
# IA(Log::Action::Save, "message %d", val) -> I("message %d", val, action=LogAction.SAVE)


# Needed only in C++
# # --- Object Lifetime Logging Functions (DOLT*, DOLTV*) ---
# def DOLTV_F(obj: object, args_str: str):
#     """
#     Display Object LifeTime Variable - Force. (Logs object creation/destruction).
#     This function is intended to be called from within __init__ or __del__.
#     """
#     if not isinstance(args_str, str): # Ensure args_str is a string
#         args_str = str(args_str)

#     try:
#         caller_frame_info = inspect.stack()[1] # Info about the direct caller (__init__ or __del__)
#         method_name = caller_frame_info.function # Should be "__init__" or "__del__"
        
#         class_name = obj.__class__.__name__ if hasattr(obj, '__class__') else "UnknownClass"
        
#         action_verb = ""
#         if method_name == "__init__":
#             action_verb = f"Creating {class_name}::{method_name}"
#         elif method_name == "__del__":
#             action_verb = f"Destroying {class_name}::{method_name}"
#         else:
#             # Fallback if called from an unexpected method
#             action_verb = f"Accessing {class_name}::{method_name}"

#         args_display = f"({args_str})" if args_str else ""
        
#         # Use id() for a memory address equivalent and hex() for similar formatting to %p
#         obj_id_hex = hex(id(obj))
        
#         log_message = f"{action_verb}{args_display}: {obj_id_hex}"
        
#         # C++ DOLTV_F uses DA (Debug with SaveSession action).
#         # We call the instance's debug method directly to provide the correct "function name" context
#         # which, in the C++ macros, is __FUNCTION__ of the constructor/destructor.
#         # Here, method_name (__init__ or __del__) serves that purpose.
#         _log_instance.debug(method_name, log_message, LogAction.SAVE_SESSION)

#     except Exception as e:
#         # Prevent logging errors from crashing the main application
#         print(f"Error in DOLTV_F: {e}", file=sys.stderr)
#         sys.stderr.flush()


# def DOLT_F(obj: object):
#     """Display Object LifeTime - Force. (No additional arguments string)."""
#     DOLTV_F(obj, "")

# def DOLTV(obj: object, args_str: str):
#     """Display Object LifeTime Variable (conditionally, based on DISPLAY_OBJECT_LIFE_TIME)."""
#     if DISPLAY_OBJECT_LIFE_TIME:
#         DOLTV_F(obj, args_str)

# def DOLT(obj: object):
#     """Display Object LifeTime (conditionally, based on DISPLAY_OBJECT_LIFE_TIME)."""
#     if DISPLAY_OBJECT_LIFE_TIME:
#         DOLT_F(obj)


# if __name__ == '__main__':
#     # Example Usage (similar to your main.cpp)
#     print("--- Python Log Class Test ---")

#     # Test basic logging
#     I("Application starting up...")
#     W("This is a sample warning, value: %d", 123)
#     E("An error occurred in %s", "module_xyz")
#     D("Debugging an intricate variable: %s", {"key": "value", "num": 42})
    
#     def another_function():
#         I("Log message from another_function.")
#         D("Debug value here: %.2f", 3.14159)
    
#     another_function()

#     R("This is a raw log message.")
#     R("Another raw message on the same line (no auto-newline for print).")
#     R("\nThis raw message starts on a new line for print.") # \n for console effect

#     # # Test Object Lifetime Logging
#     # class MyTestClass:
#     #     def __init__(self, name, value):
#     #         self.name = name
#     #         self.value = value
#     #         DOLTV(self, f"name='{self.name}', value={self.value}") # Log creation
        
#     #     def __del__(self):
#     #         DOLTV(self, f"name='{self.name}' - final state") # Log destruction
#     #         # DOLT(self) # Alternative without extra args string
        
#     #     def do_something(self):
#     #         D("MyTestClass '%s' is doing something.", self.name)

#     # print("\n--- Testing Object Lifetime ---")
#     # obj1 = MyTestClass("Object1", 100)
#     # obj1.do_something()
    
#     # obj2 = MyTestClass("Object2", {"data": [1,2,3]})
    
#     # # obj1 and obj2 will be destroyed when they go out of scope or at script end.
#     # # Explicitly delete to see __del__ logs sooner in a script.
#     # print("Deleting obj1...")
#     # del obj1 
    
#     # print("\n--- Testing Log Actions ---")
#     # I("This message uses default action (ALL)")
#     # I("This message will only be PRINTED.", action=LogAction.PRINT)
#     # W("This message will only be SAVED.", action=LogAction.SAVE)
#     # E("This message will be PRINTED and added to SESSION.", action=LogAction.PRINT_SESSION)

#     # # Retrieve and print session log
#     # session_content = _log_instance.get_current_session()
#     # print("\n--- Current Session Log Content ---")
#     # if session_content:
#     #     print(session_content)
#     # else:
#     #     print("(Session log is empty or only contained raw non-session logs)")

#     # # Test s_printf with no args
#     # I(s_printf("A pre-formatted string via s_printf"))
#     # I("A simple string, no s_printf needed")


#     # print("\n--- Test Completed ---")
#     # print(f"Log files should be in: ./{OUTPUT_DIRECTORY}")
#     # # Note: The __del__ for obj2 will likely be called when the script exits.
#     # # The order of __del__ calls at interpreter shutdown is not always predictable.
