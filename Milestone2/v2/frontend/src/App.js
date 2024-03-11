import React, { useState } from 'react';
import axios from 'axios';

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

    return (
        <div>
            <input type="text" value={query} onChange={e => setQuery(e.target.value)} />
            <button onClick={handleSearch}>Search</button>
            <ul>
                {Array.isArray(results) ? (
                    results.map((result, index) => (
                        <li key={index}>{result}</li>
                    ))
                ) : (
                    <li>No results found</li>
                )}
            </ul>
        </div>
    );
}

export default App;