# MkDocs Material Prep

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A simple but robust Python CLI tool that prepares markdown files for external publication by removing personally identifiable information (PII) and sanitizing content.

## Overview

MkDocs Material Prep helps you safely publish internal documentation by automatically detecting and removing sensitive information from markdown files. It's particularly useful when transitioning documentation from internal use to external publication.

## Features

- **PII Detection & Removal**: Automatically detects and removes emails, phone numbers, SSNs, IP addresses, and other sensitive data
- **Frontmatter Cleaning**: Removes author fields, contact information, and other PII from YAML frontmatter
- **Safe Processing**: Creates cleaned copies by default, with optional in-place editing (with automatic backups)
- **Flexible File Processing**: Supports custom file patterns and recursive directory processing
- **Configurable Rules**: Uses YAML configuration for customizable PII detection patterns
- **Contact Substitution**: Replaces personal contact information with generic alternatives
- **Dry Run Support**: Preview changes before applying them

## Installation

### From Source

```bash
git clone https://github.com/jaredm3e/mkdocs-material-prep.git
cd mkdocs-material-prep
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/jaredm3e/mkdocs-material-prep.git
cd mkdocs-material-prep
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```bash
# Process a directory and save cleaned files to output directory
python mkdocs_material_prep.py docs/ cleaned_docs/

# Process files in-place (creates .bak backups)
python mkdocs_material_prep.py docs/ -i

# Preview changes without modifying files
python mkdocs_material_prep.py docs/ output/ --dry-run
```

### Advanced Usage

```bash
# Use custom contact email for replacements
python mkdocs_material_prep.py docs/ output/ --contact "support@mycompany.com"

# Process specific file types
python mkdocs_material_prep.py docs/ output/ --pattern "*.mdx"

# Verbose output to see what's being processed
python mkdocs_material_prep.py docs/ output/ -v

# Use custom rules file
python mkdocs_material_prep.py docs/ output/ --rules custom_rules.yaml
```

## What Gets Removed/Replaced

### Frontmatter Fields
The following YAML frontmatter fields are automatically removed:
- `author`, `authors`
- `contact`, `email`
- `created_by`, `last_modified_by`
- `owner`, `maintainer`, `reviewer`
- `employee_id`, `badge_number`
- And more (see `default_rules.yaml`)

### Content Patterns
- **Email addresses**: Replaced with generic contact (default: `contact@example.com`)
- **Phone numbers**: Redacted with `[REDACTED]`
- **Social Security Numbers**: Redacted with `[REDACTED]`
- **IP addresses**: Redacted with `[REDACTED]`
- **Credit card numbers**: Redacted with `[REDACTED]`
- **Personal identifiers**: Employee IDs, badge numbers, etc.

### Example

**Before:**
```markdown
---
title: "API Documentation"
author: "John Smith"
email: "john.smith@company.com"
created_by: "Jane Doe"
---

# API Documentation

For questions, contact John Smith at john.smith@company.com or call 555-123-4567.
```

**After:**
```markdown
---
title: "API Documentation"
---

# API Documentation

For questions, contact contact@example.com or call [REDACTED].
```

## Configuration

The tool uses `default_rules.yaml` for PII detection patterns. You can customize the rules by:

1. Modifying `default_rules.yaml` directly
2. Creating a custom rules file and using `--rules custom_rules.yaml`

### Rules File Structure

```yaml
pii_patterns:
  email: '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
  phone: '\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'

frontmatter_remove:
  - author
  - email
  - created_by

substitutions:
  default_contact: "contact@example.com"
```

## CLI Reference

```
usage: mkdocs_material_prep.py [-h] [--pattern PATTERN] [--contact CONTACT] 
                               [--dry-run] [-v] [--rules RULES] [-i]
                               input_dir [output_dir]

Prepare markdown files for external publication by removing PII

positional arguments:
  input_dir            Input directory containing markdown files
  output_dir           Output directory (required unless using -i)

options:
  -h, --help           show this help message and exit
  -i, --in-place       Modify files in-place (creates .bak backups)
  --pattern PATTERN    File pattern to match (default: *.md)
  --contact CONTACT    Generic contact to replace emails (default: contact@example.com)
  --dry-run            Show what would be processed without making changes
  -v, --verbose        Verbose output
  --rules RULES        Path to rules YAML file (default: default_rules.yaml)
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest test_mkdocs_material_prep.py -v

# Run with coverage
python -m pytest test_mkdocs_material_prep.py --cov=mkdocs_material_prep

# Run specific test
python -m pytest test_mkdocs_material_prep.py::TestMarkdownProcessor::test_clean_content_email_replacement -v
```

## Project Structure

```
mkdocs-material-prep/
├── mkdocs_material_prep.py     # Main CLI script
├── default_rules.yaml          # PII detection rules
├── test_mkdocs_material_prep.py # Test suite
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── LICENSE                     # Apache 2.0 license
└── test_data/                  # Sample test files
    ├── sample_with_pii.md
    └── sample_clean.md
```

## Dependencies

- **Python 3.8+**
- **PyYAML**: For parsing YAML frontmatter and rules files

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Security Considerations

- **Review Output**: Always review the processed files before publishing
- **Test Thoroughly**: Use `--dry-run` to preview changes
- **Backup Important Files**: The tool creates backups when using `-i`, but consider additional backups for critical documents
- **Custom Patterns**: Add organization-specific PII patterns to the rules file
- **False Positives**: Some legitimate content might be flagged as PII - review and adjust rules as needed

## Changelog

### v1.0.0
- Initial release
- Core PII detection and removal functionality
- CLI interface with comprehensive options
- YAML-based configuration system
- Comprehensive test suite
- Documentation and examples

## Support

For questions, issues, or contributions, please visit the [GitHub repository](https://github.com/jaredm3e/mkdocs-material-prep).
