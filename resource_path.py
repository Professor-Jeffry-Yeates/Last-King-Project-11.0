"""Resource path helper for PyInstaller bundled applications.

This module provides a function to get the correct path to resources
whether running in development or as a bundled executable.
"""
import sys
import os

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running as a bundled executable, PyInstaller extracts files to a 
    temporary folder and stores the path in sys._MEIPASS.
    
    Args:
        relative_path: Path relative to the project root
        
    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_parent_resource_path(relative_path):
    """
    Get path to resource in parent directory, works for dev and PyInstaller.
    
    This is useful for content folders that are typically stored outside
    the main project directory.
    
    Args:
        relative_path: Path relative to the parent directory
        
    Returns:
        Absolute path to the resource
    """
    try:
        # When bundled, check if resource was included in bundle
        base_path = sys._MEIPASS
        bundled_path = os.path.join(base_path, relative_path)
        if os.path.exists(bundled_path):
            return bundled_path
        # If not in bundle, look in parent of executable location
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(os.path.dirname(exe_dir), relative_path)
    except Exception:
        # Running in development mode - use parent of current directory
        base_path = os.path.normpath(os.path.join(os.getcwd(), os.pardir))
        return os.path.join(base_path, relative_path)
