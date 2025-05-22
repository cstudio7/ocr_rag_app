# test_indexer_performance.py
import os
import time
import logging
import sys
import psutil
import datetime
from parallel_indexer import index_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("indexer_performance.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_pdf_page_count(pdf_path):
    """
    Get the number of pages in a PDF file.
    """
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            return len(pdf.pages)
    except:
        try:
            import subprocess
            # Try using pdfinfo from poppler if available
            if os.name == 'nt':  # Windows
                poppler_path = r"C:\\poppler-23.11.0\\Library\\bin"
                cmd = os.path.join(poppler_path, "pdfinfo.exe")
            else:  # Linux/Mac
                cmd = "pdfinfo"

            output = subprocess.check_output([cmd, pdf_path], universal_newlines=True)
            for line in output.splitlines():
                if "Pages:" in line:
                    return int(line.split(":")[1].strip())
        except:
            pass
    return "Unknown"

def monitor_resources(stop_event, interval=1.0):
    """
    Monitor system resources during indexing.
    """
    cpu_usage = []
    memory_usage = []

    while not stop_event.is_set():
        cpu_usage.append(psutil.cpu_percent(interval=None))
        memory_usage.append(psutil.virtual_memory().percent)
        time.sleep(interval)

    return {
        'cpu_avg': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
        'cpu_max': max(cpu_usage) if cpu_usage else 0,
        'memory_avg': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        'memory_max': max(memory_usage) if memory_usage else 0
    }

def test_indexing_performance(pdf_path):
    """
    Test the performance of the optimized PDF indexing process.

    Args:
        pdf_path: Path to the PDF file to index
    """
    if not os.path.exists(pdf_path):
        logging.error(f"❌ File not found: {pdf_path}")
        return

    # Get file size and page count
    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    page_count = get_pdf_page_count(pdf_path)

    logging.info(f"📄 Testing indexing performance for: {pdf_path}")
    logging.info(f"📊 File size: {file_size_mb:.2f} MB, Pages: {page_count}")

    # Create a report file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"indexer_report_{timestamp}.txt"

    with open(report_file, 'w') as f:
        f.write(f"PDF Indexer Performance Report\n")
        f.write(f"===========================\n\n")
        f.write(f"File: {pdf_path}\n")
        f.write(f"Size: {file_size_mb:.2f} MB\n")
        f.write(f"Pages: {page_count}\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # First run (cold start)
    logging.info("🔄 Starting first indexing run (cold start)...")

    # Start resource monitoring in a separate thread
    import threading
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=lambda: monitor_resources(stop_event),
        daemon=True
    )
    monitor_thread.start()

    start_time = time.time()
    doc_id = index_pdf(pdf_path)
    end_time = time.time()

    # Stop resource monitoring
    stop_event.set()
    monitor_thread.join(timeout=5)

    if doc_id:
        cold_time = end_time - start_time
        pages_per_second = page_count / cold_time if isinstance(page_count, int) else "Unknown"

        logging.info(f"⏱ First run (cold start) completed in {cold_time:.2f} seconds")
        logging.info(f"📈 Processing speed: {file_size_mb / cold_time:.2f} MB/s")
        if isinstance(page_count, int):
            logging.info(f"📄 Pages per second: {pages_per_second:.2f}")

        with open(report_file, 'a') as f:
            f.write(f"Cold Start Performance\n")
            f.write(f"---------------------\n")
            f.write(f"Total time: {cold_time:.2f} seconds\n")
            f.write(f"Speed: {file_size_mb / cold_time:.2f} MB/s\n")
            if isinstance(page_count, int):
                f.write(f"Pages per second: {pages_per_second:.2f}\n")
            f.write(f"CPU usage (avg): {psutil.cpu_percent()}%\n")
            f.write(f"Memory usage: {psutil.virtual_memory().percent}%\n\n")
    else:
        logging.error("❌ First run failed")
        with open(report_file, 'a') as f:
            f.write(f"Cold Start: FAILED\n\n")
        return

    # Second run (cached)
    logging.info("🔄 Starting second indexing run (with cache)...")
    start_time = time.time()
    doc_id = index_pdf(pdf_path)
    end_time = time.time()

    if doc_id:
        cached_time = end_time - start_time
        speedup = cold_time / cached_time if cached_time > 0 else float('inf')

        logging.info(f"⏱ Second run (cached) completed in {cached_time:.2f} seconds")
        logging.info(f"📈 Processing speed: {file_size_mb / cached_time:.2f} MB/s")
        logging.info(f"🚀 Speed improvement: {speedup:.2f}x faster")

        with open(report_file, 'a') as f:
            f.write(f"Cached Run Performance\n")
            f.write(f"---------------------\n")
            f.write(f"Total time: {cached_time:.2f} seconds\n")
            f.write(f"Speed: {file_size_mb / cached_time:.2f} MB/s\n")
            f.write(f"Speed improvement: {speedup:.2f}x faster\n\n")

            f.write(f"Summary\n")
            f.write(f"-------\n")
            f.write(f"The optimized indexer processed a {file_size_mb:.2f} MB PDF with {page_count} pages\n")
            f.write(f"in {cold_time:.2f} seconds on first run and {cached_time:.2f} seconds on cached run.\n")
            f.write(f"This represents a {speedup:.2f}x speedup when using the cache.\n")

        logging.info(f"📝 Performance report saved to {report_file}")
    else:
        logging.error("❌ Second run failed")
        with open(report_file, 'a') as f:
            f.write(f"Cached Run: FAILED\n")

if __name__ == "__main__":
    # Check if PDF path is provided as command line argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default PDF path if none provided
        pdf_path = os.path.join("pdfs", "sample.pdf")
        if not os.path.exists(pdf_path):
            # List available PDFs
            pdf_dir = "pdfs"
            if os.path.exists(pdf_dir):
                pdfs = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
                if pdfs:
                    pdf_path = os.path.join(pdf_dir, pdfs[0])
                    logging.info(f"📄 Using first available PDF: {pdf_path}")
                else:
                    logging.error(f"❌ No PDF files found in {pdf_dir} directory")
                    sys.exit(1)
            else:
                logging.error(f"❌ PDF directory {pdf_dir} not found")
                sys.exit(1)

    test_indexing_performance(pdf_path)
