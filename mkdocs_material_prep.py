#!/usr/bin/env python3
"""
MkDocs Material Prep - A tool to sanitize markdown files for external publication.

This tool removes personally identifiable information (PII) from markdown files
and prepares them for external publication by cleaning frontmatter and content.
"""

import argparse
import re
import shutil
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MarkdownProcessor:
    """Processes markdown files to remove PII and prepare for publication."""
    
    def __init__(self, rules_file: str = "default_rules.yaml", 
                 generic_contact: str = "contact@example.com", verbose: bool = False):
        self.generic_contact = generic_contact
        self.verbose = verbose
        self.rules = self._load_rules(rules_file)
        
    def _load_rules(self, rules_file: str) -> Dict:
        """Load PII detection rules from YAML file."""
        try:
            with open(rules_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            if self.verbose:
                print(f"Warning: Rules file {rules_file} not found, using minimal defaults")
            return self._get_default_rules()
        except yaml.YAMLError as e:
            print(f"Error parsing rules file: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        """Return minimal default rules if YAML file is not available."""
        return {
            'pii_patterns': {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            },
            'frontmatter_remove': ['author', 'authors', 'contact', 'email', 'created_by'],
            'substitutions': {
                'default_contact': 'contact@example.com'
            }
        }
    
    def _extract_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith('---\n'):
            return None, content
            
        try:
            # Find the end of frontmatter
            end_marker = content.find('\n---\n', 4)
            if end_marker == -1:
                return None, content
                
            frontmatter_text = content[4:end_marker]
            body = content[end_marker + 5:]
            
            frontmatter = yaml.safe_load(frontmatter_text)
            return frontmatter, body
        except yaml.YAMLError:
            if self.verbose:
                print("Warning: Invalid frontmatter found, skipping frontmatter processing")
            return None, content
    
    def _clean_frontmatter(self, frontmatter: Dict) -> Dict:
        """Remove PII fields from frontmatter."""
        if not frontmatter:
            return {}
            
        cleaned = frontmatter.copy()
        fields_to_remove = self.rules.get('frontmatter_remove', [])
        
        for field in fields_to_remove:
            if field in cleaned:
                if self.verbose:
                    print(f"  Removing frontmatter field: {field}")
                del cleaned[field]
        
        return cleaned
    
    def _clean_content(self, content: str) -> str:
        """Remove PII patterns from markdown content."""
        cleaned_content = content
        pii_patterns = self.rules.get('pii_patterns', {})
        
        for pattern_name, pattern in pii_patterns.items():
            matches = re.findall(pattern, cleaned_content)
            if matches:
                if self.verbose:
                    print(f"  Found {len(matches)} {pattern_name} pattern(s)")
                
                if pattern_name == 'email':
                    # Replace emails with generic contact
                    cleaned_content = re.sub(pattern, self.generic_contact, cleaned_content)
                else:
                    # Remove other PII patterns
                    cleaned_content = re.sub(pattern, '[REDACTED]', cleaned_content)
        
        return cleaned_content
    
    def _reconstruct_markdown(self, frontmatter: Optional[Dict], content: str) -> str:
        """Reconstruct markdown file with cleaned frontmatter and content."""
        if not frontmatter:
            return content
            
        # Convert frontmatter back to YAML
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_content}---\n{content}"
    
    def process_file(self, input_path: Path, output_path: Optional[Path] = None) -> bool:
        """Process a single markdown file."""
        try:
            # Read the file
            with open(input_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            if self.verbose:
                print(f"Processing: {input_path}")
            
            # Extract frontmatter and content
            frontmatter, body = self._extract_frontmatter(original_content)
            
            # Clean frontmatter
            cleaned_frontmatter = self._clean_frontmatter(frontmatter)
            
            # Clean content
            cleaned_body = self._clean_content(body)
            
            # Reconstruct the file
            final_content = self._reconstruct_markdown(cleaned_frontmatter, cleaned_body)
            
            # Determine output path
            if output_path is None:
                output_path = input_path
            
            # Write the cleaned content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            if self.verbose:
                print(f"  Saved to: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False
    
    def process_directory(self, input_dir: Path, output_dir: Optional[Path] = None, 
                         pattern: str = "*.md", in_place: bool = False, 
                         dry_run: bool = False) -> int:
        """Process all markdown files in a directory."""
        if not input_dir.exists() or not input_dir.is_dir():
            print(f"Error: Input directory {input_dir} does not exist or is not a directory")
            return 1
        
        # Find all matching files
        md_files = list(input_dir.rglob(pattern))
        if not md_files:
            print(f"No files matching pattern '{pattern}' found in {input_dir}")
            return 0
        
        if self.verbose:
            print(f"Found {len(md_files)} files to process")
        
        # Set up output directory (but not during dry run)
        if not in_place and output_dir and not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_count = 0
        
        for md_file in md_files:
            if dry_run:
                print(f"Would process: {md_file}")
                continue
            
            if in_place:
                # Create backup
                backup_path = md_file.with_suffix(md_file.suffix + '.bak')
                shutil.copy2(md_file, backup_path)
                if self.verbose:
                    print(f"  Created backup: {backup_path}")
                
                success = self.process_file(md_file)
            else:
                # Calculate relative path and create output path
                rel_path = md_file.relative_to(input_dir)
                output_path = output_dir / rel_path if output_dir else md_file.parent / f"cleaned_{md_file.name}"
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                success = self.process_file(md_file, output_path)
            
            if success:
                processed_count += 1
        
        if not dry_run:
            print(f"Successfully processed {processed_count} files")
        
        return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Prepare markdown files for external publication by removing PII",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s docs/ cleaned_docs/           # Process docs/ and save to cleaned_docs/
  %(prog)s docs/ -i                     # Process docs/ in-place (creates backups)
  %(prog)s docs/ output/ --pattern "*.mdx"  # Process .mdx files
  %(prog)s docs/ output/ --dry-run      # Show what would be processed
  %(prog)s docs/ output/ --contact "help@company.com"  # Custom contact
        """
    )
    
    parser.add_argument('input_dir', type=Path, help='Input directory containing markdown files')
    parser.add_argument('output_dir', type=Path, nargs='?', 
                       help='Output directory (required unless using -i)')
    parser.add_argument('-i', '--in-place', action='store_true',
                       help='Modify files in-place (creates .bak backups)')
    parser.add_argument('--pattern', default='*.md',
                       help='File pattern to match (default: *.md)')
    parser.add_argument('--contact', default='contact@example.com',
                       help='Generic contact to replace emails (default: contact@example.com)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without making changes')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--rules', default='default_rules.yaml',
                       help='Path to rules YAML file (default: default_rules.yaml)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.in_place and not args.output_dir:
        parser.error("Output directory is required unless using --in-place")
    
    if args.in_place and args.output_dir:
        parser.error("Cannot specify output directory when using --in-place")
    
    # Create processor
    processor = MarkdownProcessor(
        rules_file=args.rules,
        generic_contact=args.contact,
        verbose=args.verbose
    )
    
    # Process files
    return processor.process_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        pattern=args.pattern,
        in_place=args.in_place,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    sys.exit(main())
