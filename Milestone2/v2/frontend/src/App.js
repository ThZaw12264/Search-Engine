import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);

    const handleSearch = async () => {
        try {
            const response = await axios.post('http://localhost:8000/search', { query });  // Update the URL to point to the correct endpoint
            setResults(response.data);
        } catch (error) {
            console.error('Error fetching search results:', error);
        }
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="container">
            <div className="search-container">
                <input
                    className="search-input"
                    type="text"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress} // Call handleKeyPress when Enter key is pressed
                />
                <button className="search-button" onClick={handleSearch}>Search</button>
            </div>
            <ul className="results-list">
            {Array.isArray(results) ? (
                results.map((result, index) => (
                    <li key={index} className="result-item">
                        <span className="result-title">
                            {result[0]}
                        </span><br />
                        <a className="result-url" href={result[1]} target="_blank" rel="noopener noreferrer">
                            {result[1]}
                        </a>
                    </li>
                ))
            ) : (
                <li className="no-results">No results found</li>
            )}
        </ul>
        </div>
    );
}

export default App;
