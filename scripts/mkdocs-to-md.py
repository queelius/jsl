#!/usr/bin/env python3
"""
Documentation Compiler for MkDocs Projects

This script reads the mkdocs.yml configuration file and compiles all
markdown documentation into a single file, preserving the navigation
structure and hierarchy.

Usage:
    python scripts/compile_docs.py [options]

Options:
    --config PATH       Path to mkdocs.yml (default: mkdocs.yml)
    --output PATH       Output file path (default: docs/compiled/jsl-complete.md)
    --format FORMAT     Output format: markdown, pdf (default: markdown)
    --title TITLE       Document title (default: from mkdocs.yml)
    --toc              Include table of contents (default: True)
    --meta             Include metadata header (default: True)
    --separators       Include section separators (default: True)
    --verbose          Verbose output
    --help             Show this help message

Examples:
    python scripts/compile_docs.py
    python scripts/compile_docs.py --output my-docs.md --title "My Documentation"
    python scripts/compile_docs.py --format pdf --output docs.pdf
"""

import os
import sys
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Any, Optional


class DocumentationCompiler:
    """Compiles MkDocs documentation into a single file."""
    
    def __init__(self, config_path: str = "mkdocs.yml"):
        """Initialize the compiler with mkdocs config."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.docs_dir = Path("docs")  # Default docs directory
        
        # Check if custom docs_dir is specified
        if "docs_dir" in self.config:
            self.docs_dir = Path(self.config["docs_dir"])
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse mkdocs.yml configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.config_path}: {e}")
    
    def _format_title(self, name: Union[str, Dict]) -> str:
        """Convert filename or nav title to proper title case."""
        if isinstance(name, dict):
            return list(name.keys())[0]
        
        if isinstance(name, str):
            # Remove .md extension and format
            title = name.replace('.md', '').replace('-', ' ').replace('_', ' ')
            return title.title()
        
        return str(name)
    
    def _get_file_path(self, item: Union[str, Dict]) -> Optional[str]:
        """Extract file path from nav item."""
        if isinstance(item, str):
            return item
        elif isinstance(item, dict):
            value = list(item.values())[0]
            if isinstance(value, str):
                return value
        return None
    
    def _read_file_safe(self, filepath: str) -> str:
        """Safely read a markdown file with error handling."""
        full_path = self.docs_dir / filepath
        
        # Check if it's an API reference file
        if filepath.startswith('api/') and not full_path.exists():
            # Try to extract from built HTML instead
            return self._extract_from_html(filepath)
        
        if not full_path.exists():
            return f"*File not found: {filepath}*\n\n"
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Process content to adjust header levels
            return self._process_content(content)
            
        except Exception as e:
            return f"*Error reading {filepath}: {e}*\n\n"
    
    def _extract_from_html(self, html_file: str) -> str:
        """Extract content from HTML file and convert to markdown."""
        html_path = Path("site") / html_file.replace('.md', '.html')
        
        if not html_path.exists():
            return f"*HTML file not found: {html_path}*\n\n"
        
        try:
            # Try to use pandoc to convert HTML to markdown
            import subprocess
            result = subprocess.run([
                'pandoc', str(html_path), '-f', 'html', '-t', 'markdown'
            ], capture_output=True, check=True, text=True)
            
            # Clean up the converted markdown
            content = result.stdout
            # Remove navigation and footer content
            lines = content.split('\n')
            cleaned_lines = []
            in_main_content = False
            
            for line in lines:
                # Skip navigation and header content
                if 'mkdocs' in line.lower() or 'navigation' in line.lower():
                    continue
                # Start capturing after first real heading
                if line.startswith('#') and not in_main_content:
                    in_main_content = True
                if in_main_content:
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            return f"*Error extracting from HTML {html_file}: {e}*\n\n"
    
    def _process_content(self, content: str) -> str:
        """Process markdown content to adjust header levels."""
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            if line.startswith('# '):
                # Convert top-level headers to level 3 (since we use ## for sections)
                processed_lines.append('###' + line[1:])
            elif line.startswith('## '):
                # Convert level 2 headers to level 4
                processed_lines.append('####' + line[2:])
            elif line.startswith('### '):
                # Convert level 3 headers to level 5
                processed_lines.append('#####' + line[3:])
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _generate_anchor(self, title: str) -> str:
        """Generate anchor link from title."""
        return title.lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '')
    
    def _process_nav_item(self, item: Union[str, Dict], level: int = 2) -> List[str]:
        """Process a navigation item recursively."""
        output = []
        
        if isinstance(item, str):
            # Simple file reference
            title = self._format_title(os.path.basename(item).replace('.md', ''))
            output.append(f"{'#' * level} {title}\n")
            output.append(self._read_file_safe(item))
            
        elif isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    # Single file under section
                    output.append(f"{'#' * level} {key}\n")
                    output.append(self._read_file_safe(value))
                    
                elif isinstance(value, list):
                    # Section with multiple items
                    output.append(f"{'#' * level} {key}\n")
                    for sub_item in value:
                        output.extend(self._process_nav_item(sub_item, level + 1))
        
        return output
    
    def _generate_toc(self, nav_items: List) -> List[str]:
        """Generate table of contents from navigation items."""
        toc = ["## Table of Contents\n"]
        counter = 1
        
        def process_toc_item(item: Union[str, Dict], indent: str = "") -> None:
            nonlocal counter
            
            if isinstance(item, str):
                title = self._format_title(os.path.basename(item).replace('.md', ''))
                anchor = self._generate_anchor(title)
                toc.append(f"{indent}{counter}. [{title}](#{anchor})")
                counter += 1
                
            elif isinstance(item, dict):
                for key, value in item.items():
                    anchor = self._generate_anchor(key)
                    toc.append(f"{indent}{counter}. [{key}](#{anchor})")
                    counter += 1
                    
                    if isinstance(value, list):
                        for sub_item in value:
                            if isinstance(sub_item, str):
                                sub_title = self._format_title(os.path.basename(sub_item).replace('.md', ''))
                                sub_anchor = self._generate_anchor(sub_title)
                                toc.append(f"{indent}   - [{sub_title}](#{sub_anchor})")
                            elif isinstance(sub_item, dict):
                                for sub_key in sub_item.keys():
                                    sub_anchor = self._generate_anchor(sub_key)
                                    toc.append(f"{indent}   - [{sub_key}](#{sub_anchor})")
        
        for item in nav_items:
            process_toc_item(item)
        
        toc.append("")
        return toc
    
    def compile_documentation(self, 
                            output_path: str = "docs/compiled/jsl-complete.md",
                            title: Optional[str] = None,
                            include_toc: bool = True,
                            include_meta: bool = True,
                            include_separators: bool = True,
                            verbose: bool = False) -> str:
        """Compile all documentation into a single markdown file."""
        
        if verbose:
            print(f"Loading configuration from: {self.config_path}")
            print(f"Documentation directory: {self.docs_dir}")
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build the document
        lines = []
        
        # Document header
        doc_title = title or self.config.get('site_name', 'Documentation')
        lines.append(f"# {doc_title}\n")
        
        if include_meta:
            site_description = self.config.get('site_description', '')
            if site_description:
                lines.append(f"*{site_description}*\n")
            
            lines.append("**Complete Documentation**\n")
            lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if include_separators:
                lines.append("---\n")
        
        # Table of contents
        nav_items = self.config.get('nav', [])
        if include_toc and nav_items:
            lines.extend(self._generate_toc(nav_items))
            if include_separators:
                lines.append("---\n")
        
        # Process navigation items
        for item in nav_items:
            if verbose:
                if isinstance(item, dict):
                    print(f"Processing section: {list(item.keys())[0]}")
                else:
                    print(f"Processing item: {item}")
            
            content_lines = self._process_nav_item(item)
            lines.extend(content_lines)
            
            if include_separators and content_lines:
                lines.append("---\n")
        
        # Footer
        lines.append("*End of Documentation*\n")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        if verbose:
            file_size = output_file.stat().st_size
            line_count = len(lines)
            print(f"\n✓ Documentation compiled successfully!")
            print(f"✓ Output file: {output_file}")
            print(f"✓ File size: {file_size:,} bytes")
            print(f"✓ Line count: {line_count:,} lines")
        
        return str(output_file)
    
    def compile_to_pdf(self, 
                      output_path: str = "docs/compiled/jsl-complete.pdf",
                      title: Optional[str] = None,
                      verbose: bool = False) -> str:
        """Compile documentation to PDF using pandoc."""
        try:
            import subprocess
        except ImportError:
            raise ImportError("subprocess module required for PDF generation")
        
        # First compile to markdown
        md_path = output_path.replace('.pdf', '.md')
        self.compile_documentation(md_path, title, verbose=verbose)
        
        # Check if pandoc is available and get version
        try:
            result = subprocess.run(['pandoc', '--version'], capture_output=True, check=True, text=True)
            if verbose:
                version_line = result.stdout.split('\n')[0]
                print(f"Found pandoc: {version_line}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Pandoc not found. Install with:\n"
                             "  Ubuntu/Debian: sudo apt install pandoc texlive-xetex\n"
                             "  macOS: brew install pandoc basictex\n"
                             "  Windows: Download from https://pandoc.org/installing.html")
        
        # Convert to PDF with more compatible options
        doc_title = title or self.config.get('site_name', 'Documentation')
        author = self.config.get('site_author', 'Generated Documentation')
        
        # Try different PDF engines in order of preference
        pdf_engines = ['xelatex', 'pdflatex', 'lualatex']
        highlight_styles = ['tango', 'kate', 'espresso', 'zenburn', 'haddock']
        
        for engine in pdf_engines:
            for highlight in highlight_styles:
                pandoc_cmd = [
                    'pandoc', md_path, '-o', output_path,
                    f'--pdf-engine={engine}',
                    '--toc',
                    '--number-sections',
                    f'--highlight-style={highlight}',
                    '-V', 'geometry:margin=1in',
                    '-V', 'fontsize=11pt',
                    '-V', 'documentclass=article',
                    '-V', f'title={doc_title}',
                    '-V', f'author={author}',
                    '-V', f'date={datetime.now().strftime("%Y-%m-%d")}',
                    '--standalone'
                ]
                
                if verbose:
                    print(f"Trying PDF engine: {engine} with highlight: {highlight}")
                
                try:
                    result = subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True)
                    if verbose:
                        pdf_size = Path(output_path).stat().st_size
                        print(f"✓ PDF generated successfully!")
                        print(f"✓ Engine used: {engine}")
                        print(f"✓ Highlight style: {highlight}")
                        print(f"✓ Output: {output_path}")
                        print(f"✓ Size: {pdf_size:,} bytes")
                    return output_path
                    
                except subprocess.CalledProcessError as e:
                    if verbose:
                        print(f"  Failed with {engine}/{highlight}: {e.stderr}")
                    continue
        
        # If all engines failed, try a minimal command
        minimal_cmd = [
            'pandoc', md_path, '-o', output_path,
            '--toc',
            '-V', f'title={doc_title}',
            '-V', f'author={author}'
        ]
        
        if verbose:
            print("Trying minimal pandoc command...")
            print(f"Command: {' '.join(minimal_cmd)}")
        
        try:
            subprocess.run(minimal_cmd, check=True, capture_output=True, text=True)
            if verbose:
                print("✓ PDF generated with minimal options")
            return output_path
        except subprocess.CalledProcessError as e:
            # Provide detailed error information
            error_msg = f"Pandoc failed with all attempted configurations.\n"
            error_msg += f"Last error: {e.stderr}\n"
            error_msg += f"Return code: {e.returncode}\n\n"
            error_msg += "Troubleshooting suggestions:\n"
            error_msg += "1. Install required LaTeX packages:\n"
            error_msg += "   Ubuntu/Debian: sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra\n"
            error_msg += "   macOS: brew install --cask mactex\n"
            error_msg += "2. Try generating markdown only: --format markdown\n"
            error_msg += "3. Check pandoc installation: pandoc --version\n"
            raise RuntimeError(error_msg)

    def get_available_highlight_styles(self) -> List[str]:
        """Get available highlight styles from pandoc."""
        try:
            import subprocess
            result = subprocess.run(['pandoc', '--list-highlight-styles'], 
                                  capture_output=True, check=True, text=True)
            return result.stdout.strip().split('\n')
        except:
            return ['tango', 'kate', 'espresso', 'zenburn', 'haddock']

    def get_available_pdf_engines(self) -> List[str]:
        """Get available PDF engines from pandoc."""
        try:
            import subprocess
            # Test which engines are available
            engines = ['xelatex', 'pdflatex', 'lualatex', 'wkhtmltopdf']
            available = []
            
            for engine in engines:
                try:
                    subprocess.run([engine, '--version'], 
                                 capture_output=True, check=True)
                    available.append(engine)
                except:
                    continue
            
            return available if available else ['pdflatex']  # fallback
        except:
            return ['pdflatex']
    
    def diagnose_pandoc(self) -> None:
        """Diagnose pandoc installation and capabilities."""
        try:
            import subprocess
        except ImportError:
            print("❌ subprocess module not available")
            return
        
        print("🔧 Pandoc Diagnostic Report")
        print("=" * 40)
        
        # Check pandoc installation
        try:
            result = subprocess.run(['pandoc', '--version'], capture_output=True, check=True, text=True)
            version_info = result.stdout.split('\n')[0]
            print(f"✓ Pandoc found: {version_info}")
        except FileNotFoundError:
            print("❌ Pandoc not found")
            print("   Install: sudo apt install pandoc (Ubuntu) or brew install pandoc (Mac)")
            return
        except subprocess.CalledProcessError as e:
            print(f"❌ Pandoc error: {e}")
            return
        
        # Check available highlight styles
        try:
            result = subprocess.run(['pandoc', '--list-highlight-styles'], 
                                  capture_output=True, check=True, text=True)
            styles = result.stdout.strip().split('\n')
            print(f"✓ Available highlight styles ({len(styles)}): {', '.join(styles[:5])}...")
        except:
            print("⚠ Could not get highlight styles")
        
        # Check PDF engines
        engines = ['xelatex', 'pdflatex', 'lualatex', 'wkhtmltopdf']
        available_engines = []
        
        for engine in engines:
            try:
                subprocess.run([engine, '--version'], capture_output=True, check=True)
                available_engines.append(engine)
            except:
                continue
        
        if available_engines:
            print(f"✓ Available PDF engines: {', '.join(available_engines)}")
        else:
            print("❌ No PDF engines found")
            print("   Install LaTeX: sudo apt install texlive-xetex (Ubuntu) or brew install basictex (Mac)")
        
        # Check LaTeX installation
        try:
            subprocess.run(['latex', '--version'], capture_output=True, check=True)
            print("✓ LaTeX found")
        except:
            print("⚠ LaTeX not found (needed for PDF generation)")
        
        print("\n🎯 Recommendations:")
        if not available_engines:
            print("- Install a LaTeX distribution for PDF support")
        if 'github' not in styles:
            print("- Use 'tango' or 'kate' instead of 'github' highlight style")
        print("- Try markdown format first: --format markdown")
    
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Compile MkDocs documentation into a single file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('\n\n')[1]  # Use the examples from docstring
    )
    
    parser.add_argument(
        '--config', 
        default='mkdocs.yml',
        help='Path to mkdocs.yml (default: mkdocs.yml)'
    )
    
    parser.add_argument(
        '--output',
        default='docs/compiled/jsl-complete.md',
        help='Output file path (default: docs/compiled/jsl-complete.md)'
    )
    
    parser.add_argument(
        '--format',
        choices=['markdown', 'pdf'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--title',
        help='Document title (default: from mkdocs.yml)'
    )
    
    parser.add_argument(
        '--no-toc',
        action='store_true',
        help='Skip table of contents generation'
    )
    
    parser.add_argument(
        '--no-meta',
        action='store_true',
        help='Skip metadata header'
    )
    
    parser.add_argument(
        '--no-separators',
        action='store_true',
        help='Skip section separators'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--diagnose',
        action='store_true',
        help='Diagnose pandoc installation and exit'
    )

    args = parser.parse_args()
    
    if args.diagnose:
        compiler = DocumentationCompiler(args.config)
        compiler.diagnose_pandoc()
        return
    
    try:
        compiler = DocumentationCompiler(args.config)
        
        if args.format == 'pdf':
            output_file = compiler.compile_to_pdf(
                output_path=args.output,
                title=args.title,
                verbose=args.verbose
            )
        else:
            output_file = compiler.compile_documentation(
                output_path=args.output,
                title=args.title,
                include_toc=not args.no_toc,
                include_meta=not args.no_meta,
                include_separators=not args.no_separators,
                verbose=args.verbose
            )
        
        if not args.verbose:
            print(f"✓ Documentation compiled: {output_file}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
