"""CodeQL Wrapper package."""

DEFAULT_AUTHORS = "Mateus Perdigão Domiciano; Fernando Matsuo Santos"
DEFAULT_EMAILS = "mateus.domiciano@moduscreate.com; fernando.matsuo@moduscreate.com"

try:
    from importlib.metadata import metadata, version

    # Get package metadata
    pkg_metadata = metadata("codeql-wrapper")
    __version__ = version("codeql-wrapper")

    # Extract author and email from metadata
    authors = pkg_metadata.get("Author", "")
    author_email = pkg_metadata.get("Author-email", "")

    # Parse author and email from the authors field if available
    # Note: importlib.metadata only returns the first author, so we use our constants
    # to ensure both authors are properly credited
    if authors or author_email:
        # Package metadata is available, but use our complete author info
        __author__ = DEFAULT_AUTHORS
        __email__ = DEFAULT_EMAILS
    else:
        __author__ = DEFAULT_AUTHORS
        __email__ = DEFAULT_EMAILS
except Exception:
    # Fallback values if package metadata is not available
    __version__ = "0.0.0"
    __author__ = DEFAULT_AUTHORS
    __email__ = DEFAULT_EMAILS
