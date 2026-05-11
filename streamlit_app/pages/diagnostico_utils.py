"""
Utility functions for diagnostico page import and file verification.
"""

import sys
import traceback
from pathlib import Path


def run_import_test(test_config: dict) -> tuple[bool, str | None]:
    """
    Run an import test based on configuration.
    
    Args:
        test_config: Dictionary with 'module', 'imports', 'test_code' keys
        
    Returns:
        Tuple of (success: bool, error_message: str | None)
    """
    try:
        # Import the module
        module_name = test_config.get("module")
        __import__(module_name)
        return True, None
    except Exception as e:
        return False, traceback.format_exc()


def verify_files(project_root: Path, files_list: list[str]) -> list[tuple[str, bool]]:
    """
    Verify that specified files exist in project.
    
    Args:
        project_root: Root path of the project
        files_list: List of relative file paths to check
        
    Returns:
        List of tuples (file_path, exists: bool)
    """
    results = []
    for file_path in files_list:
        full_path = project_root / file_path
        exists = full_path.exists()
        results.append((file_path, exists))
    return results


def get_relevant_modules() -> list[str]:
    """
    Get loaded modules relevant to the system (core, streamlit_app, proceso).
    
    Returns:
        Sorted list of module names
    """
    relevant_modules = [
        m
        for m in sys.modules.keys()
        if "core" in m or "streamlit_app" in m or "proceso" in m
    ]
    return sorted(relevant_modules)
