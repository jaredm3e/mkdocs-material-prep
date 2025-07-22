#!/usr/bin/env python3
"""
Test suite for mkdocs_material_prep.py

Run with: python -m pytest test_mkdocs_material_prep.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from mkdocs_material_prep import MarkdownProcessor


class TestMarkdownProcessor:
    """Test cases for the MarkdownProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.processor = MarkdownProcessor(verbose=True)
        
    def teardown_method(self):
        """Clean up after each test method."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_extract_frontmatter_valid(self):
        """Test extracting valid YAML frontmatter."""
        content = """---
title: "Test Document"
author: "John Doe"
email: "john@example.com"
---

# Test Content

This is the body of the document.
"""
        frontmatter, body = self.processor._extract_frontmatter(content)
        
        assert frontmatter is not None
        assert frontmatter['title'] == "Test Document"
        assert frontmatter['author'] == "John Doe"
        assert frontmatter['email'] == "john@example.com"
        assert body.strip() == "# Test Content\n\nThis is the body of the document."
    
    def test_extract_frontmatter_none(self):
        """Test content without frontmatter."""
        content = "# Test Document\n\nThis has no frontmatter."
        frontmatter, body = self.processor._extract_frontmatter(content)
        
        assert frontmatter is None
        assert body == content
    
    def test_extract_frontmatter_invalid(self):
        """Test invalid YAML frontmatter."""
        content = """---
title: "Test Document
invalid: yaml: content
---

# Test Content
"""
        frontmatter, body = self.processor._extract_frontmatter(content)
        
        # Should return None for invalid YAML
        assert frontmatter is None
        assert body == content
    
    def test_clean_frontmatter(self):
        """Test removing PII fields from frontmatter."""
        frontmatter = {
            'title': 'Test Document',
            'author': 'John Doe',
            'email': 'john@example.com',
            'created_by': 'Jane Smith',
            'description': 'A test document',
            'version': '1.0'
        }
        
        cleaned = self.processor._clean_frontmatter(frontmatter)
        
        # Should remove PII fields but keep others
        assert 'title' in cleaned
        assert 'description' in cleaned
        assert 'version' in cleaned
        assert 'author' not in cleaned
        assert 'email' not in cleaned
        assert 'created_by' not in cleaned
    
    def test_clean_frontmatter_empty(self):
        """Test cleaning empty frontmatter."""
        cleaned = self.processor._clean_frontmatter(None)
        assert cleaned == {}
        
        cleaned = self.processor._clean_frontmatter({})
        assert cleaned == {}
    
    def test_clean_content_email_replacement(self):
        """Test replacing email addresses in content."""
        content = """
        Contact john.doe@company.com for support.
        Also reach out to support@example.org.
        """
        
        cleaned = self.processor._clean_content(content)
        
        # Emails should be replaced with generic contact
        assert "john.doe@company.com" not in cleaned
        assert "support@example.org" not in cleaned
        assert "contact@example.com" in cleaned
    
    def test_clean_content_phone_redaction(self):
        """Test redacting phone numbers in content."""
        content = """
        Call us at 555-123-4567 or (555) 987-6543.
        International: +1-555-111-2222
        """
        
        cleaned = self.processor._clean_content(content)
        
        # Phone numbers should be redacted
        assert "555-123-4567" not in cleaned
        assert "(555) 987-6543" not in cleaned
        assert "+1-555-111-2222" not in cleaned
        assert "[REDACTED]" in cleaned
    
    def test_clean_content_multiple_patterns(self):
        """Test cleaning content with multiple PII patterns."""
        content = """
        Contact: john@company.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        Server: 192.168.1.100
        """
        
        cleaned = self.processor._clean_content(content)
        
        # Email should be replaced, others redacted
        assert "john@company.com" not in cleaned
        assert "contact@example.com" in cleaned
        assert "555-123-4567" not in cleaned
        assert "123-45-6789" not in cleaned
        assert "192.168.1.100" not in cleaned
        assert "[REDACTED]" in cleaned
    
    def test_reconstruct_markdown_with_frontmatter(self):
        """Test reconstructing markdown with frontmatter."""
        frontmatter = {'title': 'Test', 'version': '1.0'}
        content = "# Test Content\n\nBody text."
        
        result = self.processor._reconstruct_markdown(frontmatter, content)
        
        assert result.startswith("---\n")
        assert "title: Test" in result
        assert "version: '1.0'" in result
        assert result.endswith("---\n# Test Content\n\nBody text.")
    
    def test_reconstruct_markdown_without_frontmatter(self):
        """Test reconstructing markdown without frontmatter."""
        content = "# Test Content\n\nBody text."
        
        result = self.processor._reconstruct_markdown(None, content)
        
        assert result == content
    
    def test_process_file_with_pii(self):
        """Test processing a file containing PII."""
        # Create test file
        test_file = self.temp_dir / "test.md"
        content = """---
title: "Test Document"
author: "John Doe"
email: "john@company.com"
---

# Test Document

Contact john@company.com for questions.
Call 555-123-4567 for support.
"""
        test_file.write_text(content)
        
        # Process the file
        output_file = self.temp_dir / "output.md"
        success = self.processor.process_file(test_file, output_file)
        
        assert success
        assert output_file.exists()
        
        # Check the processed content
        processed_content = output_file.read_text()
        assert "author: John Doe" not in processed_content
        assert "email: john@company.com" not in processed_content
        assert "john@company.com" not in processed_content
        assert "555-123-4567" not in processed_content
        assert "contact@example.com" in processed_content
        assert "[REDACTED]" in processed_content
    
    def test_process_file_clean_content(self):
        """Test processing a file with no PII."""
        # Create clean test file
        test_file = self.temp_dir / "clean.md"
        content = """---
title: "Clean Document"
version: "1.0"
---

# Clean Document

This document contains no PII.
"""
        test_file.write_text(content)
        
        # Process the file
        output_file = self.temp_dir / "output.md"
        success = self.processor.process_file(test_file, output_file)
        
        assert success
        assert output_file.exists()
        
        # Content should be mostly unchanged (except formatting)
        processed_content = output_file.read_text()
        assert "title: Clean Document" in processed_content
        assert "version: '1.0'" in processed_content
        assert "This document contains no PII." in processed_content
    
    def test_process_file_in_place(self):
        """Test processing a file in-place."""
        # Create test file
        test_file = self.temp_dir / "test.md"
        original_content = """---
author: "John Doe"
---

Contact john@example.com
"""
        test_file.write_text(original_content)
        
        # Process in-place
        success = self.processor.process_file(test_file)
        
        assert success
        
        # Check the file was modified
        processed_content = test_file.read_text()
        assert "author: John Doe" not in processed_content
        assert "john@example.com" not in processed_content
        assert "contact@example.com" in processed_content
    
    def test_process_directory_basic(self):
        """Test processing a directory of markdown files."""
        # Create test files
        (self.temp_dir / "file1.md").write_text("---\nauthor: John\n---\nContent")
        (self.temp_dir / "file2.md").write_text("# Clean file")
        (self.temp_dir / "file3.txt").write_text("Not a markdown file")
        
        # Create output directory
        output_dir = self.temp_dir / "output"
        
        # Process directory
        result = self.processor.process_directory(self.temp_dir, output_dir)
        
        assert result == 0  # Success
        assert output_dir.exists()
        assert (output_dir / "file1.md").exists()
        assert (output_dir / "file2.md").exists()
        assert not (output_dir / "file3.txt").exists()  # Should not process .txt files
        
        # Check processed content
        processed = (output_dir / "file1.md").read_text()
        assert "author: John" not in processed
    
    def test_process_directory_in_place(self):
        """Test processing directory in-place with backups."""
        # Create test files
        test_file = self.temp_dir / "test.md"
        test_file.write_text("---\nauthor: John\n---\nContent")
        
        # Process in-place
        result = self.processor.process_directory(self.temp_dir, in_place=True)
        
        assert result == 0
        
        # Check backup was created
        backup_file = self.temp_dir / "test.md.bak"
        assert backup_file.exists()
        
        # Check original file was modified
        processed_content = test_file.read_text()
        assert "author: John" not in processed_content
        
        # Check backup contains original content
        backup_content = backup_file.read_text()
        assert "author: John" in backup_content
    
    def test_process_directory_custom_pattern(self):
        """Test processing directory with custom file pattern."""
        # Create test files
        (self.temp_dir / "file1.md").write_text("# Markdown file")
        (self.temp_dir / "file2.mdx").write_text("# MDX file")
        (self.temp_dir / "file3.txt").write_text("# Text file")
        
        output_dir = self.temp_dir / "output"
        
        # Process with custom pattern
        result = self.processor.process_directory(
            self.temp_dir, output_dir, pattern="*.mdx"
        )
        
        assert result == 0
        assert (output_dir / "file2.mdx").exists()
        assert not (output_dir / "file1.md").exists()
        assert not (output_dir / "file3.txt").exists()
    
    def test_process_directory_dry_run(self):
        """Test dry run functionality."""
        # Create test file
        (self.temp_dir / "test.md").write_text("---\nauthor: John\n---\nContent")
        
        output_dir = self.temp_dir / "output"
        
        # Run dry run
        result = self.processor.process_directory(
            self.temp_dir, output_dir, dry_run=True
        )
        
        assert result == 0
        # Output directory should not be created in dry run
        assert not output_dir.exists()
    
    def test_process_directory_nonexistent(self):
        """Test processing non-existent directory."""
        nonexistent_dir = self.temp_dir / "nonexistent"
        output_dir = self.temp_dir / "output"
        
        result = self.processor.process_directory(nonexistent_dir, output_dir)
        
        assert result == 1  # Error code
    
    def test_process_directory_no_files(self):
        """Test processing directory with no matching files."""
        # Create directory with no .md files
        (self.temp_dir / "file.txt").write_text("Not markdown")
        
        output_dir = self.temp_dir / "output"
        
        result = self.processor.process_directory(self.temp_dir, output_dir)
        
        assert result == 0  # Success, but no files processed
    
    def test_custom_contact_replacement(self):
        """Test using custom contact email for replacements."""
        processor = MarkdownProcessor(generic_contact="support@mycompany.com")
        
        content = "Contact john@example.com for help."
        cleaned = processor._clean_content(content)
        
        assert "john@example.com" not in cleaned
        assert "support@mycompany.com" in cleaned
    
    def test_load_rules_file_not_found(self):
        """Test loading rules when file doesn't exist."""
        processor = MarkdownProcessor(rules_file="nonexistent.yaml")
        
        # Should fall back to default rules
        assert 'pii_patterns' in processor.rules
        assert 'email' in processor.rules['pii_patterns']
    
    def test_load_rules_invalid_yaml(self):
        """Test loading invalid YAML rules file."""
        # Create invalid YAML file
        invalid_yaml = self.temp_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        processor = MarkdownProcessor(rules_file=str(invalid_yaml))
        
        # Should fall back to default rules
        assert 'pii_patterns' in processor.rules
        assert 'email' in processor.rules['pii_patterns']


class TestCLIIntegration:
    """Integration tests for the CLI interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up after tests."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_cli_basic_usage(self):
        """Test basic CLI usage."""
        # Create test file
        input_dir = self.temp_dir / "input"
        input_dir.mkdir()
        (input_dir / "test.md").write_text("---\nauthor: John\n---\nContent")
        
        output_dir = self.temp_dir / "output"
        
        # Import and test main function
        from mkdocs_material_prep import main
        import sys
        
        # Mock sys.argv
        original_argv = sys.argv
        try:
            sys.argv = ['mkdocs_material_prep.py', str(input_dir), str(output_dir)]
            result = main()
            assert result == 0
            assert (output_dir / "test.md").exists()
        finally:
            sys.argv = original_argv


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
