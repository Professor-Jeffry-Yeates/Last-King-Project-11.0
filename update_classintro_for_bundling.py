"""
Optional: Update ClassIntro.py to support bundled resources

This script shows the changes needed if you want to support BOTH:
1. Running from source (development)
2. Running as bundled executable (production)

ONLY USE THIS IF YOU CHOSE OPTION A (bundling content with executable)

Steps:
1. Review the changes below
2. Make a backup of ClassIntro.py: copy ClassIntro.py ClassIntro.py.backup
3. Apply the changes manually OR run this script
4. Test both modes: python MapSetup.py AND dist/MapSetup.exe
"""

import os
import shutil

def backup_file(filepath):
    """Create a backup of the file."""
    backup_path = filepath + '.backup'
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"✓ Created backup: {backup_path}")
        return True
    else:
        print(f"⚠ Backup already exists: {backup_path}")
        response = input("Overwrite? (y/n): ")
        if response.lower() == 'y':
            shutil.copy2(filepath, backup_path)
            print(f"✓ Overwrote backup: {backup_path}")
            return True
        return False

def show_changes():
    """Display the changes that need to be made."""
    print("\n" + "="*70)
    print("CHANGES NEEDED IN ClassIntro.py")
    print("="*70)
    
    print("\n1. ADD import at the top (after existing imports):")
    print("-" * 70)
    print("from resource_path import get_parent_resource_path")
    
    print("\n2. REPLACE this line (around line 17):")
    print("-" * 70)
    print("OLD:")
    print("    upOneDirectory = os.path.normpath(os.path.join( os.getcwd(), os.pardir))")
    print("\nNEW:")
    print("    upOneDirectory = get_parent_resource_path('')")
    
    print("\n" + "="*70)
    print("WHAT THIS DOES:")
    print("="*70)
    print("• In development: Looks in parent directory (normal behavior)")
    print("• In executable: Looks in bundled resources or next to .exe")
    print("• Supports both modes automatically!")
    print("="*70)
    print()

def apply_changes():
    """Apply the changes to ClassIntro.py."""
    filepath = 'ClassIntro.py'
    
    if not os.path.exists(filepath):
        print(f"✗ Error: {filepath} not found in current directory")
        print(f"  Current directory: {os.getcwd()}")
        return False
    
    # Create backup
    if not backup_file(filepath):
        print("✗ Backup failed, aborting changes")
        return False
    
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track changes
    changes_made = 0
    
    # Add import (after other imports, before class definition)
    import_line = "from resource_path import get_parent_resource_path\n"
    import_added = False
    for i, line in enumerate(lines):
        if 'class ClassIntro' in line and not import_added:
            # Insert before class definition
            if import_line not in lines:
                lines.insert(i, import_line)
                print("✓ Added import statement")
                changes_made += 1
                import_added = True
            break
    
    # Replace the path line
    old_pattern = "os.path.normpath(os.path.join( os.getcwd(), os.pardir))"
    new_code = "get_parent_resource_path('')"
    
    for i, line in enumerate(lines):
        if old_pattern in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + f"upOneDirectory = {new_code}\n"
            print("✓ Updated path resolution")
            changes_made += 1
            break
    
    if changes_made > 0:
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"\n✓ Successfully applied {changes_made} change(s) to {filepath}")
        print(f"✓ Backup saved as: {filepath}.backup")
        return True
    else:
        print("\n⚠ No changes made - pattern not found or already updated")
        return False

def main():
    print("="*70)
    print("ClassIntro.py Resource Path Update Tool")
    print("="*70)
    print()
    print("This tool updates ClassIntro.py to work with bundled executables.")
    print()
    print("⚠ WARNING: This will modify ClassIntro.py")
    print("  A backup will be created automatically")
    print()
    
    show_changes()
    
    response = input("Apply these changes now? (y/n): ")
    
    if response.lower() == 'y':
        print("\nApplying changes...")
        success = apply_changes()
        
        if success:
            print("\n" + "="*70)
            print("NEXT STEPS:")
            print("="*70)
            print("1. Test in development mode:")
            print("   python MapSetup.py")
            print()
            print("2. Build executable:")
            print("   build_executable.bat")
            print()
            print("3. Test bundled executable:")
            print("   cd dist")
            print("   MapSetup.exe")
            print()
            print("If something goes wrong, restore backup:")
            print("   copy ClassIntro.py.backup ClassIntro.py")
            print("="*70)
        else:
            print("\n✗ Changes failed - ClassIntro.py not modified")
    else:
        print("\nNo changes made. You can apply them manually using the guide above.")
        print("See DATA_FILES_CONFIG.md for detailed instructions.")

if __name__ == "__main__":
    main()
    print()
    input("Press Enter to exit...")
