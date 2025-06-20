
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faFileAlt, faStar } from '@fortawesome/free-solid-svg-icons';

// Helper function to escape regex special characters
const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

// Component to highlight text with search terms
const HighlightedText = ({ text, searchTerms }) => {
  if (!searchTerms || searchTerms.length === 0 || !text) {
    return <span>{text}</span>;
  }

  // Create regex for the exact query (all terms together)
  const exactQuery = searchTerms.join(' ');
  const exactQueryRegex = new RegExp(escapeRegExp(exactQuery), 'gi');
  
  // Create regex for individual terms
  const termRegexes = searchTerms
    .filter(term => term.length > 1)
    .map(term => new RegExp(`\\b${escapeRegExp(term)}\\b`, 'gi'));

  // First split by exact matches
  const parts = text.split(exactQueryRegex);
  
  // Process each part to highlight individual terms
  const processedParts = parts.map((part, index) => {
    // Every odd index is an exact match
    if (index % 2 === 1) {
      return <mark key={`exact-${index}`} className="exact-match">{part}</mark>;
    }
    
    // For non-exact matches, check for individual terms
    let processedPart = part;
    let lastIndex = 0;
    const segments = [];
    
    // Process each term
    termRegexes.forEach(regex => {
      let match;
      while ((match = regex.exec(part)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
          segments.push(part.substring(lastIndex, match.index));
        }
        
        // Add the highlighted match
        segments.push(
          <mark key={`term-${match.index}`} className="term-match">
            {match[0]}
          </mark>
        );
        
        lastIndex = match.index + match[0].length;
      }
    });
    
    // Add any remaining text
    if (lastIndex < part.length) {
      segments.push(part.substring(lastIndex));
    }
    
    return segments.length > 0 ? segments : part;
  });
  
  return <>{processedParts}</>;
};

function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [correctedQuery, setCorrectedQuery] = useState(null);
  const [hasCorrections, setHasCorrections] = useState(false);
  const [searchTerms, setSearchTerms] = useState([]);

  const handleSearch = async (e, useOriginal = false) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    
    try {
      const response = await axios.post('/api/query', {
        query: query.trim(),
        use_original: useOriginal
      });
      
      setResults(response.data.results || []);
      setCorrectedQuery(response.data.corrected_query);
      setHasCorrections(response.data.has_corrections || false);
      
      // Set search terms for highlighting
      const terms = query.trim().split(/\s+/).filter(term => term.length > 1);
      setSearchTerms(terms);
      
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUseOriginal = (e) => {
    handleSearch(e, true);
  };

  return (
    <div className="container search-container">
      <h1 className="mb-4">
        <FontAwesomeIcon icon={faSearch} className="me-2" />
        Search Knowledge Base
      </h1>
      
      <form onSubmit={handleSearch} className="mb-4">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder="Enter your search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            <FontAwesomeIcon icon={faSearch} className="me-2" />
            Search
          </button>
        </div>
      </form>
      
      {hasCorrections && correctedQuery && (
        <div className="alert alert-info">
          <p>
            Showing results for <strong>{correctedQuery}</strong>
            <button 
              className="btn btn-sm btn-link" 
              onClick={handleUseOriginal}
            >
              Search for "{query}" instead
            </button>
          </p>
        </div>
      )}
      
      {loading ? (
        <div className="text-center my-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      ) : (
        <>
          <h2 className="mb-3">Results</h2>
          
          {results.length === 0 ? (
            <div className="alert alert-warning">
              No results found for your query.
            </div>
          ) : (
            <div className="results-list">
              {results.map((result, index) => (
                <div key={index} className="card result-card mb-3">
                  <div className="card-header d-flex justify-content-between">
                    <div>
                      <FontAwesomeIcon icon={faFileAlt} className="me-2" />
                      {result.document}
                    </div>
                    <div>
                      <FontAwesomeIcon icon={faStar} className="me-1" />
                      {Math.round(result.similarity)}% Match
                    </div>
                  </div>
                  <div className="card-body">
                    <div className="result-text">
                      <HighlightedText 
                        text={result.text} 
                        searchTerms={searchTerms} 
                      />
                    </div>
                    <div className="result-meta mt-2">
                      <small className="text-muted">
                        <FontAwesomeIcon icon={faFileAlt} className="me-1" />
                        Document: {result.document} | Page: {result.page}
                      </small>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Search;
