#!/usr/bin/env python3
"""
Test that web_gui.py has valid syntax and our new functions are defined correctly
"""

import ast
import sys

def test_web_gui_syntax():
    """Test that web_gui.py has valid Python syntax"""
    print("Testing web_gui.py syntax...")
    
    try:
        with open('web_gui.py', 'r') as f:
            code = f.read()
        
        # Parse the code to check for syntax errors
        ast.parse(code)
        print("✓ web_gui.py has valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in web_gui.py: {e}")
        return False

def test_functions_defined():
    """Test that our new functions are defined in web_gui.py"""
    print("Checking for required functions...")
    
    try:
        with open('web_gui.py', 'r') as f:
            code = f.read()
        
        required_functions = [
            'ensure_user_data_dir',
            'save_avatar',
            'load_avatar',
            'save_background',
            'load_background',
            'load_user_images_on_startup'
        ]
        
        for func_name in required_functions:
            if f'def {func_name}(' in code:
                print(f"  ✓ {func_name} is defined")
            else:
                print(f"  ✗ {func_name} is NOT defined")
                return False
        
        print("✓ All required functions are defined")
        return True
    except Exception as e:
        print(f"✗ Error checking functions: {e}")
        return False

def test_constants_defined():
    """Test that required constants are defined"""
    print("Checking for required constants...")
    
    try:
        with open('web_gui.py', 'r') as f:
            code = f.read()
        
        required_constants = [
            'USER_DATA_DIR',
            'AVATAR_PATH',
            'BACKGROUND_PATH'
        ]
        
        for const_name in required_constants:
            if const_name in code:
                print(f"  ✓ {const_name} is defined")
            else:
                print(f"  ✗ {const_name} is NOT defined")
                return False
        
        print("✓ All required constants are defined")
        return True
    except Exception as e:
        print(f"✗ Error checking constants: {e}")
        return False

def test_startup_call():
    """Test that load_user_images_on_startup is called in main()"""
    print("Checking for startup call...")
    
    try:
        with open('web_gui.py', 'r') as f:
            code = f.read()
        
        if 'load_user_images_on_startup()' in code:
            # Check if it's in the main function
            main_func_start = code.find('def main():')
            if main_func_start != -1:
                # Find the next function definition (end of main)
                next_func = code.find('\ndef ', main_func_start + 10)
                if next_func == -1:
                    next_func = len(code)
                
                main_func_code = code[main_func_start:next_func]
                if 'load_user_images_on_startup()' in main_func_code:
                    print("  ✓ load_user_images_on_startup() is called in main()")
                    return True
                else:
                    print("  ✗ load_user_images_on_startup() is NOT called in main()")
                    return False
        
        print("  ✗ load_user_images_on_startup() call not found")
        return False
    except Exception as e:
        print(f"✗ Error checking startup call: {e}")
        return False

def test_save_calls_in_callbacks():
    """Test that save functions are called in the upload callbacks"""
    print("Checking for save calls in callbacks...")
    
    try:
        with open('web_gui.py', 'r') as f:
            code = f.read()
        
        # Check for save_avatar call in update_avatar callback
        if 'save_avatar(contents)' in code or 'save_avatar(' in code:
            print("  ✓ save_avatar() is called")
        else:
            print("  ✗ save_avatar() is NOT called")
            return False
        
        # Check for save_background call in update_background callback
        if 'save_background(contents)' in code or 'save_background(' in code:
            print("  ✓ save_background() is called")
        else:
            print("  ✗ save_background() is NOT called")
            return False
        
        print("✓ Save functions are properly called in callbacks")
        return True
    except Exception as e:
        print(f"✗ Error checking save calls: {e}")
        return False

def test_gitignore_updated():
    """Test that .gitignore includes user_data/"""
    print("Checking .gitignore...")
    
    try:
        with open('.gitignore', 'r') as f:
            content = f.read()
        
        if 'user_data/' in content:
            print("  ✓ user_data/ is in .gitignore")
            return True
        else:
            print("  ✗ user_data/ is NOT in .gitignore")
            return False
    except Exception as e:
        print(f"✗ Error checking .gitignore: {e}")
        return False

def test_env_example_updated():
    """Test that .env.example includes USER_PROFILE_* variables"""
    print("Checking .env.example...")
    
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        has_name = 'USER_PROFILE_NAME' in content
        has_username = 'USER_PROFILE_USERNAME' in content
        
        if has_name:
            print("  ✓ USER_PROFILE_NAME is in .env.example")
        else:
            print("  ✗ USER_PROFILE_NAME is NOT in .env.example")
        
        if has_username:
            print("  ✓ USER_PROFILE_USERNAME is in .env.example")
        else:
            print("  ✗ USER_PROFILE_USERNAME is NOT in .env.example")
        
        if has_name and has_username:
            print("✓ .env.example is properly updated")
            return True
        return False
    except Exception as e:
        print(f"✗ Error checking .env.example: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("Running Code Validation Tests")
    print("="*60)
    
    all_passed = True
    
    all_passed &= test_web_gui_syntax()
    print()
    all_passed &= test_functions_defined()
    print()
    all_passed &= test_constants_defined()
    print()
    all_passed &= test_startup_call()
    print()
    all_passed &= test_save_calls_in_callbacks()
    print()
    all_passed &= test_gitignore_updated()
    print()
    all_passed &= test_env_example_updated()
    
    print("="*60)
    if all_passed:
        print("All validation tests passed! ✓")
        print("="*60)
        sys.exit(0)
    else:
        print("Some tests failed! ✗")
        print("="*60)
        sys.exit(1)
