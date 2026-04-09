#!/usr/bin/env python3
"""Comprehensive document encoding fixer"""

import os
import glob
import chardet
from pathlib import Path


def detect_encoding(file_path):
    """Detect file encoding using chardet"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'], result['confidence']
    except Exception as e:
        print(f"Error detecting encoding for {file_path}: {e}")
        return None, 0


def read_with_encoding(file_path, encoding):
    """Read file with specified encoding"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path} with {encoding}: {e}")
        return None


def fix_encoding(file_path, target_encoding='utf-8'):
    """Fix file encoding"""
    print(f"Processing: {file_path}")
    
    # Detect current encoding
    current_encoding, confidence = detect_encoding(file_path)
    print(f"  Current encoding: {current_encoding} (confidence: {confidence:.2f})")
    
    if not current_encoding:
        print(f"  ERROR: Could not detect encoding")
        return False
    
    # Read content
    content = read_with_encoding(file_path, current_encoding)
    if content is None:
        # Try fallback encodings
        fallback_encodings = ['utf-8', 'gbk', 'gb18030', 'latin-1']
        for enc in fallback_encodings:
            if enc != current_encoding:
                content = read_with_encoding(file_path, enc)
                if content is not None:
                    print(f"  Fallback to {enc} encoding")
                    break
    
    if content is None:
        print(f"  ERROR: Could not read file with any encoding")
        return False
    
    # Write back with target encoding
    try:
        with open(file_path, 'w', encoding=target_encoding) as f:
            f.write(content)
        print(f"  Successfully converted to {target_encoding}")
        return True
    except Exception as e:
        print(f"  ERROR: Could not write file: {e}")
        return False


def main():
    """Main function"""
    docs_dir = Path(__file__).parent / "docs"
    markdown_files = list(docs_dir.rglob('*.md'))
    
    print(f"Found {len(markdown_files)} markdown files")
    print("=" * 60)
    
    fixed_count = 0
    error_count = 0
    
    for file_path in markdown_files:
        if fix_encoding(file_path):
            fixed_count += 1
        else:
            error_count += 1
        print("-" * 60)
    
    print("=" * 60)
    print(f"Summary:")
    print(f"  Fixed: {fixed_count} files")
    print(f"  Errors: {error_count} files")


if __name__ == "__main__":
    main()
