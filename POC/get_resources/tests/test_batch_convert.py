"""Tests for batch PDF conversion with concurrent processing."""
from __future__ import annotations

import pathlib
import sys
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# Add Docling directory to path
_docling_dir = pathlib.Path(__file__).parent.parent / "Docling"
sys.path.insert(0, str(_docling_dir))

from batch_convert import (
    ProcessingResult,
    find_pdfs,
    get_worker_count,
    is_processed,
    make_slug,
    process_single_pdf,
)


class TestSlugGeneration:
    """Test PDF filename to slug conversion."""

    def test_basic_filename(self):
        """Test basic filename conversion."""
        pdf_path = pathlib.Path("Test_Document.pdf")
        assert make_slug(pdf_path) == "test_document"

    def test_complex_filename(self):
        """Test complex filename with version and special chars."""
        pdf_path = pathlib.Path("XS2A-API-as-PSD2-v2.4.0.pdf")
        assert make_slug(pdf_path) == "xs2a_api_as_psd2_v2_4_0"

    def test_multiple_underscores_collapsed(self):
        """Test that multiple non-alphanumeric chars collapse to single underscore."""
        pdf_path = pathlib.Path("Test___Document--2024.pdf")
        assert make_slug(pdf_path) == "test_document_2024"

    def test_leading_trailing_stripped(self):
        """Test leading/trailing underscores are stripped."""
        pdf_path = pathlib.Path("_Test_Document_.pdf")
        assert make_slug(pdf_path) == "test_document"


class TestProcessedCheck:
    """Test detection of already-processed PDFs."""

    def test_processed_file_exists(self, tmp_path):
        """Test returns True when cleaned markdown exists."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        clean_file = spec_dir / "test_doc_clean.md"
        clean_file.write_text("# Test")
        
        assert is_processed("test_doc", spec_dir) is True

    def test_processed_file_missing(self, tmp_path):
        """Test returns False when cleaned markdown does not exist."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        
        assert is_processed("test_doc", spec_dir) is False

    def test_spec_dir_missing(self, tmp_path):
        """Test returns False when spec directory does not exist."""
        spec_dir = tmp_path / "nonexistent"
        
        assert is_processed("test_doc", spec_dir) is False


class TestCopyCleanedMarkdown:
    """Test copying cleaned markdown to specification directory - REMOVED.
    
    This functionality has been eliminated - files are now written directly
    to the final destination without intermediate copying.
    """
    pass


class TestFindPdfs:
    """Test PDF discovery."""

    def test_find_single_pdf(self, tmp_path):
        """Test finding single PDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        
        pdfs = find_pdfs(tmp_path)
        
        assert len(pdfs) == 1
        assert pdfs[0] == pdf_file

    def test_find_multiple_pdfs(self, tmp_path):
        """Test finding multiple PDFs."""
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        pdf1.write_bytes(b"%PDF")
        pdf2.write_bytes(b"%PDF")
        
        pdfs = find_pdfs(tmp_path)
        
        assert len(pdfs) == 2
        assert pdf1 in pdfs
        assert pdf2 in pdfs

    def test_find_pdfs_recursive(self, tmp_path):
        """Test recursive PDF discovery."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = subdir / "test2.pdf"
        pdf1.write_bytes(b"%PDF")
        pdf2.write_bytes(b"%PDF")
        
        pdfs = find_pdfs(tmp_path)
        
        assert len(pdfs) == 2
        assert pdf1 in pdfs
        assert pdf2 in pdfs

    def test_find_no_pdfs(self, tmp_path):
        """Test returns empty list when no PDFs found."""
        (tmp_path / "test.txt").write_text("not a pdf")
        
        pdfs = find_pdfs(tmp_path)
        
        assert pdfs == []

    def test_results_sorted(self, tmp_path):
        """Test that results are sorted."""
        pdf_c = tmp_path / "c.pdf"
        pdf_a = tmp_path / "a.pdf"
        pdf_b = tmp_path / "b.pdf"
        for pdf in [pdf_c, pdf_a, pdf_b]:
            pdf.write_bytes(b"%PDF")
        
        pdfs = find_pdfs(tmp_path)
        
        assert pdfs == [pdf_a, pdf_b, pdf_c]


class TestWorkerCount:
    """Test worker count computation."""

    def test_explicit_worker_count(self):
        """Test explicit worker count is used."""
        assert get_worker_count(4) == 4
        assert get_worker_count(8) == 8

    def test_auto_worker_count(self):
        """Test auto worker count (CPU count - 1)."""
        with patch("multiprocessing.cpu_count", return_value=8):
            assert get_worker_count(0) == 7

    def test_minimum_one_worker(self):
        """Test minimum of 1 worker even on single-core systems."""
        with patch("multiprocessing.cpu_count", return_value=1):
            assert get_worker_count(0) == 1

    def test_dual_core_system(self):
        """Test dual-core system returns 1 worker."""
        with patch("multiprocessing.cpu_count", return_value=2):
            assert get_worker_count(0) == 1


class TestProcessSinglePdf:
    """Test single PDF processing."""

    def test_process_success(self, tmp_path):
        """Test successful PDF processing."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir(parents=True)
        
        with patch("batch_convert.build_converter") as mock_build:
            with patch("batch_convert.convert_pdf") as mock_convert:
                with patch("batch_convert.postprocess_pdf") as mock_postprocess:
                    mock_converter = Mock()
                    mock_build.return_value = mock_converter
                    mock_convert.return_value = "# Test Markdown"
                    
                    result = process_single_pdf(pdf_path, spec_dir, "none")
        
        slug = "test"
        mock_convert.assert_called_once()
        mock_postprocess.assert_called_once_with("# Test Markdown", slug, spec_dir)
        
        assert result.status == "success"
        assert result.pdf_name == "test.pdf"
        assert result.slug == "test"
        assert result.error_message is None
        assert result.elapsed_seconds is not None
        assert result.elapsed_seconds > 0

    def test_process_skipped(self, tmp_path):
        """Test skipping already-processed PDF."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        
        # Create cleaned markdown to simulate already processed
        slug = "test"
        clean_file = spec_dir / f"{slug}_clean.md"
        clean_file.write_text("# Existing")
        
        result = process_single_pdf(pdf_path, spec_dir, "none")
        
        assert result.status == "skipped"
        assert result.pdf_name == "test.pdf"
        assert result.error_message is None

    def test_process_failure(self, tmp_path):
        """Test failed PDF processing."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF")
        spec_dir = tmp_path / "specs"
        
        with patch("batch_convert.build_converter") as mock_build:
            with patch("batch_convert.convert_pdf", side_effect=Exception("Conversion error")):
                mock_build.return_value = Mock()
                
                result = process_single_pdf(pdf_path, spec_dir, "none")
        
        assert result.status == "failed"
        assert result.pdf_name == "test.pdf"
        assert result.error_message == "Conversion error"
        assert result.elapsed_seconds is not None


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_multiple_pdfs_isolated_failures(self, tmp_path):
        """Test that failure in one PDF doesn't affect others."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir(parents=True)
        
        pdf1 = tmp_path / "success.pdf"
        pdf2 = tmp_path / "failure.pdf"
        pdf1.write_bytes(b"%PDF")
        pdf2.write_bytes(b"%PDF")
        
        def convert_side_effect(converter, pdf_path, slug, output_dir, mode):
            if "failure" in pdf_path.name:
                raise Exception("Simulated failure")
            return "# Success Markdown"
        
        with patch("batch_convert.build_converter", return_value=Mock()):
            with patch("batch_convert.convert_pdf", side_effect=convert_side_effect):
                with patch("batch_convert.postprocess_pdf"):
                    result1 = process_single_pdf(pdf1, spec_dir, "none")
                    result2 = process_single_pdf(pdf2, spec_dir, "none")
        
        assert result1.status == "success"
        assert result2.status == "failed"

    def test_deterministic_output_filenames(self, tmp_path):
        """Test that output filenames are deterministic."""
        spec_dir = tmp_path / "specs"
        
        pdf_path = tmp_path / "XS2A-API-v2.4.pdf"
        pdf_path.write_bytes(b"%PDF")
        
        slug = make_slug(pdf_path)
        spec_dir.mkdir(parents=True)
        (spec_dir / f"{slug}_clean.md").write_text("# Content")
        
        with patch("batch_convert.build_converter", return_value=Mock()):
            with patch("batch_convert.convert_pdf"):
                with patch("batch_convert.postprocess_pdf"):
                    result = process_single_pdf(pdf_path, spec_dir, "none")
        
        assert result.slug == "xs2a_api_v2_4"
        expected_output = spec_dir / "xs2a_api_v2_4_clean.md"
        assert expected_output.exists()
