#!/usr/bin/env python3
# This file uses PyQt6
"""
FFmpeg Unzipper CLI Tool
Unzips FFmpeg components to the specified directories.
"""

import os
import zipfile
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


def create_directory_if_not_exists(directory_path):
    """Create directory if it doesn't exist."""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory created/verified: {directory_path}")
        return True
    except FileNotFoundError:
        print(f"✗ Directory path not found: {directory_path}")
        return False
    except PermissionError:
        print(f"✗ No permission to create directory: {directory_path}")
        return False
    except OSError as e:
        print(f"✗ OS error creating directory {directory_path}: {e}")
        return False


def unzip_file(zip_path, extract_path, description):
    """Unzip a file to the specified path."""
    try:
        if not os.path.exists(zip_path):
            print(f"✗ Error: {zip_path} not found")
            return False
        
        print(f"📦 Extracting {description}...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        print(f"✓ Successfully extracted {description} to {extract_path}")
        return True
        
    except FileNotFoundError:
        print(f"✗ Zip file not found: {zip_path}")
        return False
    except PermissionError:
        print(f"✗ No permission to extract zip file: {zip_path}")
        return False
    except zipfile.BadZipFile as e:
        print(f"✗ Bad zip file {zip_path}: {e}")
        return False
    except OSError as e:
        print(f"✗ OS error extracting {description}: {e}")
        return False


def show_success_dialog(base_dir, bin_dir):
    """Show a success dialog with the extraction results."""
    try:
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Show success message
        message = f"""💫 FFmpeg Setup Complete!

All files have been extracted successfully!

📂 Installation Directory: {base_dir}
🔧 Executables Location: {bin_dir}

FFmpeg is now ready to use!"""
        
        messagebox.showinfo("FFmpeg Unzipper - Success", message)
        
        # Destroy the root window
        root.destroy()
        
    except tk.TclError as e:
        print(f"Could not show dialog: {e}")
        # Fallback to console message if dialog fails


def main():
    """Main function to handle the unzipping process."""
    print("🚀 FFmpeg Unzipper CLI Tool")
    print("=" * 40)
    
    # Define the base directory
    base_dir = r"C:\SuperCut\ffmpeg"
    bin_dir = os.path.join(base_dir, "bin")
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    if not create_directory_if_not_exists(base_dir):
        sys.exit(1)
    
    if not create_directory_if_not_exists(bin_dir):
        sys.exit(1)
    
    # Define unzipping tasks
    tasks = [
        {
            "zip_path": "sources/ffmpeg-folder.zip",
            "extract_path": base_dir,
            "description": "FFmpeg folder"
        },
        {
            "zip_path": "sources/ffmpeg.zip",
            "extract_path": bin_dir,
            "description": "FFmpeg executable"
        },
        {
            "zip_path": "sources/ffplay.zip",
            "extract_path": bin_dir,
            "description": "FFplay executable"
        },
        {
            "zip_path": "sources/ffprobe.zip",
            "extract_path": bin_dir,
            "description": "FFprobe executable"
        }
    ]
    
    # Execute unzipping tasks
    print("\n📦 Starting extraction process...")
    success_count = 0
    
    for task in tasks:
        if unzip_file(task["zip_path"], task["extract_path"], task["description"]):
            success_count += 1
        print()  # Add spacing between tasks
    
    # Show final results
    print("=" * 40)
    if success_count == len(tasks):
        print("💫 All files extracted successfully!")
        print(f"📂 FFmpeg components are now available in: {base_dir}")
        print(f"🔧 Executables are located in: {bin_dir}")
        
        # Show success dialog
        show_success_dialog(base_dir, bin_dir)
    else:
        print(f"⚠️  {success_count}/{len(tasks)} files extracted successfully.")
        print("Please check the error messages above for details.")
    
    print("\n✨ FFmpeg setup complete!")


if __name__ == "__main__":
    main() 