#!/usr/bin/env python3
"""
Translation Compiler Utility

A utility tool for compiling PO files to MO files with proper UTF-8 encoding support.
This tool provides functions to compile individual language files or all translation files at once.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from babel.messages import pofile, mofile


class TranslationCompiler:
    """Handles compilation of PO files to MO files for internationalization."""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the translation compiler.
        
        Args:
            base_dir: Base directory of the project. If None, auto-detects from current file location.
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent

        self.base_dir = base_dir
        self.locale_dir = base_dir / 'locale'
        self.domain = 'if_gen_tool'

    def compile_po_to_mo(self, po_path: Path, mo_path: Path, language: str = None) -> bool:
        """
        Compile a single PO file to MO file using Babel.
        
        Args:
            po_path: Path to the PO file
            mo_path: Path to the output MO file
            language: Language name for logging (optional)
            
        Returns:
            bool: True if compilation successful, False otherwise
        """
        try:
            # Ensure PO file exists
            if not po_path.exists():
                print(f"❌ PO file not found: {po_path}")
                return False

            # Create MO directory if it doesn't exist
            mo_path.parent.mkdir(parents=True, exist_ok=True)

            # Read PO file with proper encoding
            with open(po_path, 'rb') as f:
                catalog = pofile.read_po(f)

            # Write MO file with proper encoding
            with open(mo_path, 'wb') as f:
                mofile.write_mo(f, catalog)

            lang_display = language or po_path.parent.parent.name
            print(f"✅ Successfully compiled {lang_display}: {po_path.name} -> {mo_path.name}")
            return True

        except Exception as e:
            lang_display = language or po_path.parent.parent.name
            print(f"❌ Error compiling {lang_display} translation {po_path}: {e}")
            return False

    def get_language_files(self) -> List[Tuple[Path, Path, str]]:
        """
        Get all available language PO/MO file pairs.
        
        Returns:
            List of tuples: (po_path, mo_path, language_code)
        """
        language_files = []

        if not self.locale_dir.exists():
            print(f"❌ Locale directory not found: {self.locale_dir}")
            return language_files

        # Scan for language directories
        for lang_dir in self.locale_dir.iterdir():
            if lang_dir.is_dir() and lang_dir.name != '__pycache__':
                lc_messages_dir = lang_dir / 'LC_MESSAGES'
                if lc_messages_dir.exists():
                    po_path = lc_messages_dir / f'{self.domain}.po'
                    mo_path = lc_messages_dir / f'{self.domain}.mo'

                    if po_path.exists():
                        language_files.append((po_path, mo_path, lang_dir.name))

        return language_files

    def compile_language(self, language_code: str) -> bool:
        """
        Compile MO file for a specific language.
        
        Args:
            language_code: Language code (e.g., 'en', 'zh', 'ja')
            
        Returns:
            bool: True if compilation successful, False otherwise
        """
        po_path = self.locale_dir / language_code / 'LC_MESSAGES' / f'{self.domain}.po'
        mo_path = self.locale_dir / language_code / 'LC_MESSAGES' / f'{self.domain}.mo'

        if not po_path.exists():
            print(f"❌ PO file not found for language '{language_code}': {po_path}")
            return False

        return self.compile_po_to_mo(po_path, mo_path, language_code)

    def compile_all_languages(self) -> Tuple[int, int]:
        """
        Compile MO files for all available languages.
        
        Returns:
            Tuple[int, int]: (successful_count, total_count)
        """
        language_files = self.get_language_files()

        if not language_files:
            print("❌ No language files found to compile.")
            return 0, 0

        print(f"🔄 Compiling {len(language_files)} language file(s)...\n")

        success_count = 0
        for po_path, mo_path, language_code in language_files:
            if self.compile_po_to_mo(po_path, mo_path, language_code):
                success_count += 1
            print()  # Add spacing between languages

        print(f"📊 Summary: {success_count}/{len(language_files)} language file(s) compiled successfully!")

        if success_count == len(language_files):
            print("🎉 All translation files compiled successfully!")
        elif success_count > 0:
            print("⚠️  Some translation files failed to compile. Please check the errors above.")
        else:
            print("❌ All compilation attempts failed. Please check your PO files and dependencies.")

        return success_count, len(language_files)

    def list_languages(self) -> List[str]:
        """
        List all available language codes.
        
        Returns:
            List of language codes
        """
        language_files = self.get_language_files()
        return [lang_code for _, _, lang_code in language_files]

    def validate_babel_dependency(self) -> bool:
        """
        Validate that Babel is installed and available.
        
        Returns:
            bool: True if Babel is available, False otherwise
        """
        try:
            import babel.messages.pofile
            import babel.messages.mofile
            return True
        except ImportError:
            print("❌ Babel library not found. Please install it with: pip install babel")
            return False


def compile_translations(language: Optional[str] = None, base_dir: Optional[Path] = None) -> bool:
    """
    Convenience function to compile translation files.
    
    Args:
        language: Specific language to compile (e.g., 'en', 'zh', 'ja'). If None, compiles all languages.
        base_dir: Base directory of the project. If None, auto-detects.
        
    Returns:
        bool: True if all compilations successful, False otherwise
    """
    compiler = TranslationCompiler(base_dir)

    # Validate dependencies
    if not compiler.validate_babel_dependency():
        return False

    if language:
        # Compile specific language
        return compiler.compile_language(language)
    else:
        # Compile all languages
        success_count, total_count = compiler.compile_all_languages()
        return success_count == total_count


def main():
    """Command line entry point for the translation compiler."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compile PO files to MO files for internationalization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python translation_compiler.py                    # Compile all languages
  python translation_compiler.py --language en     # Compile English only
  python translation_compiler.py --language zh     # Compile Chinese only
  python translation_compiler.py --language ja     # Compile Japanese only
  python translation_compiler.py --list            # List available languages
        """
    )

    parser.add_argument(
        "--language", "-l",
        type=str,
        help="Compile specific language (e.g., en, zh, ja)"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available languages"
    )

    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Base directory of the project (auto-detects if not specified)"
    )

    args = parser.parse_args()

    try:
        compiler = TranslationCompiler(args.base_dir)

        # Validate dependencies
        if not compiler.validate_babel_dependency():
            return 1

        if args.list:
            # List available languages
            languages = compiler.list_languages()
            if languages:
                print("📋 Available languages:")
                for lang in sorted(languages):
                    print(f"  • {lang}")
            else:
                print("❌ No language files found.")
            return 0

        # Compile translations
        if compile_translations(args.language, args.base_dir):
            return 0
        else:
            return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
